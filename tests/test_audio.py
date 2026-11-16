import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.audio import make_voice, _subtitle_cues


class FakeCommunicate:
    def __init__(self, text, voice, rate="+0%"):
        self.text = text
        self.voice = voice
        self.rate = rate
        type(self).last_rate = rate

    async def stream(self):
        yield {"type": "audio", "data": b"fake-mp3"}
        yield {
            "type": "WordBoundary",
            "offset": 0,
            "duration": 5_000_000,
            "text": "Olá",
        }
        yield {
            "type": "WordBoundary",
            "offset": 5_000_000,
            "duration": 5_000_000,
            "text": "mundo.",
        }


class AudioSubtitleTests(unittest.TestCase):
    def test_builds_srt_directly_from_word_boundaries(self):
        with tempfile.TemporaryDirectory(prefix="nexus_audio_test_") as temp:
            output = Path(temp) / "voice.mp3"
            with patch("nexus.audio.edge_tts.Communicate", FakeCommunicate):
                audio_path, subtitle_path = make_voice(
                    "Olá mundo.", "pt-BR-AntonioNeural", output
                )

            self.assertEqual(audio_path.read_bytes(), b"fake-mp3")
            self.assertEqual(FakeCommunicate.last_rate, "+0%")
            content = subtitle_path.read_text(encoding="utf-8")
            self.assertIn("00:00:00,000 --> 00:00:01,000", content)
            self.assertIn("Olá mundo.", " ".join(content.split()))
            self.assertNotIn("\\n", content)
            self.assertGreaterEqual(len(content.splitlines()), 3)
            self.assertTrue(content.startswith("1\n"))
            self.assertEqual(subtitle_path.suffix, ".srt")

    def test_falls_back_to_sentence_boundaries(self):
        events = [{
            "type": "SentenceBoundary",
            "offset": 0,
            "duration": 12_000_000,
            "text": "Uma frase completa.",
        }]
        cues = _subtitle_cues(events, "Uma frase completa.")
        self.assertGreaterEqual(len(cues), 1)
        self.assertEqual(" ".join(" ".join(cue[2].split()) for cue in cues), "Uma frase completa.")

    def test_prefers_sentence_boundaries_over_single_word_events(self):
        events = [
            {"type": "WordBoundary", "offset": i * 500 * 10_000,
             "duration": 400 * 10_000, "text": word}
            for i, word in enumerate(["Esta", "é", "uma", "frase", "inteira."])
        ]
        events.append({
            "type": "SentenceBoundary", "offset": 0,
            "duration": 2_500 * 10_000, "text": "Esta é uma frase inteira."
        })
        cues = _subtitle_cues(events, "Esta é uma frase inteira.")
        self.assertEqual(len(cues), 1)
        self.assertEqual(" ".join(cues[0][2].split()), "Esta é uma frase inteira.")

    def test_falls_back_to_estimated_captions_without_timing_events(self):
        cues = _subtitle_cues([], "Uma narração sem eventos de sincronização.")
        self.assertTrue(cues)
        self.assertIn("narração", " ".join(cue[2] for cue in cues))

    def test_captions_are_short_phrases_with_at_most_two_lines(self):
        words = ["A", "mudança", "começa", "quando", "você", "decide", "agir", "mesmo", "com", "medo", "e", "continua"]
        events = [
            {
                "type": "WordBoundary",
                "offset": index * 450 * 10_000,
                "duration": 400 * 10_000,
                "text": word,
            }
            for index, word in enumerate(words)
        ]
        cues = _subtitle_cues(events, " ".join(words))
        self.assertGreater(len(cues), 1)
        for _, _, caption in cues:
            self.assertLessEqual(len(caption.splitlines()), 2)
            self.assertLessEqual(len(caption.split()), 7)

    def test_captions_are_short_phrases_with_at_most_two_lines(self):
        words = ["A", "mudança", "começa", "quando", "você", "decide", "agir", "mesmo", "com", "medo", "e", "continua"]
        events = [
            {
                "type": "WordBoundary",
                "offset": index * 450 * 10_000,
                "duration": 400 * 10_000,
                "text": word,
            }
            for index, word in enumerate(words)
        ]
        cues = _subtitle_cues(events, " ".join(words))
        self.assertGreater(len(cues), 1)
        for _, _, caption in cues:
            self.assertLessEqual(len(caption.splitlines()), 2)
            self.assertLessEqual(len(caption.split()), 7)


if __name__ == "__main__":
    unittest.main()


class FakeFishResponse:
    def raise_for_status(self):
        return None

    def iter_lines(self, decode_unicode=True):
        import base64
        import json
        yield "data: " + json.dumps({
            "audio_base64": base64.b64encode(b"fish-mp3").decode("ascii"),
            "alignment": {"segments": [
                {"text": "Olá", "start": 0.0, "end": 0.4},
                {"text": "mundo.", "start": 0.4, "end": 0.9},
            ]},
        })
        yield "data: [DONE]"


class FakeFishSession:
    def __init__(self):
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return FakeFishResponse()


class FishAudioTests(unittest.TestCase):
    def test_fish_audio_writes_mp3_and_native_word_timestamp_subtitles(self):
        session = FakeFishSession()
        with tempfile.TemporaryDirectory(prefix="nexus_fish_test_") as temp:
            output = Path(temp) / "voice.mp3"
            audio_path, subtitle_path = make_voice(
                "Olá mundo.", "pt-BR-AntonioNeural", output,
                fish_api_key="test-key", session=session
            )
            self.assertEqual(audio_path.read_bytes(), b"fish-mp3")
            srt = subtitle_path.read_text(encoding="utf-8")
            self.assertIn("Olá mundo.", " ".join(srt.splitlines()[2:]))
            self.assertIn("00:00:00,000 --> 00:00:00,900", srt)
        args, kwargs = session.calls[0]
        self.assertIn("/v1/tts/stream/with-timestamp", args[0])
        self.assertEqual(kwargs["headers"]["model"], "s2.1-pro-free")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")

    def test_fish_audio_failure_falls_back_to_edge_tts(self):
        class BrokenFishSession:
            def post(self, *args, **kwargs):
                raise RuntimeError("provider unavailable")
        with tempfile.TemporaryDirectory(prefix="nexus_fish_fallback_") as temp:
            output = Path(temp) / "voice.mp3"
            with patch("nexus.audio.edge_tts.Communicate", FakeCommunicate):
                audio_path, subtitle_path = make_voice(
                    "Olá mundo.", "pt-BR-AntonioNeural", output,
                    fish_api_key="test-key", session=BrokenFishSession()
                )
            self.assertEqual(audio_path.read_bytes(), b"fake-mp3")
            self.assertTrue(subtitle_path.exists())
