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
            self.assertIn("Olá mundo.", content)
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
        self.assertEqual(" ".join(cue[2] for cue in cues), "Uma frase completa.")

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
            self.assertLessEqual(len(caption.split()), 4)

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
            self.assertLessEqual(len(caption.split()), 4)


if __name__ == "__main__":
    unittest.main()
