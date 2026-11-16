import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.audio import make_voice, _subtitle_cues


class FakeCommunicate:
    def __init__(self, text, voice):
        self.text = text
        self.voice = voice

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
    def test_builds_srt_without_submaker_api(self):
        with tempfile.TemporaryDirectory(prefix="nexus_audio_test_") as temp:
            output = Path(temp) / "voice.mp3"
            with patch("nexus.audio.edge_tts.Communicate", FakeCommunicate):
                audio_path, subtitle_path = make_voice(
                    "Olá mundo.", "pt-BR-AntonioNeural", output
                )

            self.assertEqual(audio_path.read_bytes(), b"fake-mp3")
            content = subtitle_path.read_text(encoding="utf-8")
            self.assertIn("00:00:00,000 --> 00:00:01,000", content)
            self.assertIn("Olá mundo.", content)
            self.assertEqual(subtitle_path.suffix, ".srt")

    def test_falls_back_to_sentence_boundaries(self):
        events = [{
            "type": "SentenceBoundary",
            "offset": 0,
            "duration": 12_000_000,
            "text": "Uma frase completa.",
        }]
        cues = _subtitle_cues(events, "Uma frase completa.")
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0][2], "Uma frase completa.")

    def test_falls_back_to_estimated_captions_without_timing_events(self):
        cues = _subtitle_cues([], "Uma narração sem eventos de sincronização.")
        self.assertTrue(cues)
        self.assertIn("narração", " ".join(cue[2] for cue in cues))


if __name__ == "__main__":
    unittest.main()
