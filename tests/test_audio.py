import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.audio import make_voice


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


class ModernSubMaker:
    def __init__(self):
        self.events = []

    def feed(self, chunk):
        self.events.append(chunk)

    def get_srt(self):
        return "1\\n00:00:00,000 --> 00:00:00,500\\nOlá\\n"


class LegacySubMaker:
    def __init__(self):
        self.events = []

    def create_sub(self, timestamp, text):
        self.events.append((timestamp, text))

    def generate_subs(self):
        return "1\\n00:00:00,000 --> 00:00:00,500\\nOlá\\n"


class AudioSubtitleCompatibilityTests(unittest.TestCase):
    def _run_with_submaker(self, maker_class):
        maker = maker_class()
        with tempfile.TemporaryDirectory(prefix="nexus_audio_test_") as temp:
            output = Path(temp) / "voice.mp3"
            with patch("nexus.audio.edge_tts.Communicate", FakeCommunicate), \\
                 patch("nexus.audio.edge_tts.SubMaker", return_value=maker):
                audio_path, subtitle_path = make_voice(
                    "Olá", "pt-BR-AntonioNeural", output
                )

            self.assertEqual(audio_path.read_bytes(), b"fake-mp3")
            self.assertIn("Olá", subtitle_path.read_text(encoding="utf-8"))
            self.assertEqual(subtitle_path.suffix, ".srt")
            self.assertEqual(len(maker.events), 1)
            return maker

    def test_supports_current_feed_and_get_srt_api(self):
        maker = self._run_with_submaker(ModernSubMaker)
        self.assertEqual(maker.events[0]["type"], "WordBoundary")

    def test_supports_legacy_create_sub_and_generate_subs_api(self):
        maker = self._run_with_submaker(LegacySubMaker)
        self.assertEqual(maker.events[0][1], "Olá")


if __name__ == "__main__":
    unittest.main()
