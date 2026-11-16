import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.audio import make_voice


class FakeCommunicate:
    last_rate = None

    def __init__(self, text, voice, rate="+0%"):
        self.text = text
        self.voice = voice
        self.rate = rate
        type(self).last_rate = rate

    async def stream(self):
        yield {"type": "audio", "data": b"fake-mp3"}


class FakeFishResponse:
    def raise_for_status(self):
        return None

    def iter_lines(self, decode_unicode=True):
        import base64
        import json
        yield "data: " + json.dumps({
            "audio_base64": base64.b64encode(b"fish-mp3").decode("ascii"),
            "alignment": {"segments": [{"text": "ignored", "start": 0, "end": 1}]},
        })
        yield "data: [DONE]"


class FakeFishSession:
    def post(self, *args, **kwargs):
        self.calls = getattr(self, "calls", [])
        self.calls.append((args, kwargs))
        return FakeFishResponse()


class AudioOutputTests(unittest.TestCase):
    def test_edge_tts_generates_audio_without_subtitle_file(self):
        with tempfile.TemporaryDirectory(prefix="nexus_audio_test_") as temp:
            output = Path(temp) / "voice.mp3"
            with patch("nexus.audio.edge_tts.Communicate", FakeCommunicate):
                audio_path = make_voice("Olá mundo.", "pt-BR-AntonioNeural", output)
            self.assertEqual(audio_path.read_bytes(), b"fake-mp3")
            self.assertEqual(FakeCommunicate.last_rate, "+0%")
            self.assertFalse(output.with_suffix(".srt").exists())

    def test_fish_audio_generates_audio_only_and_reports_provider(self):
        session = FakeFishSession()
        with tempfile.TemporaryDirectory(prefix="nexus_fish_test_") as temp:
            output = Path(temp) / "voice.mp3"
            audio_path, provider = make_voice(
                "Olá mundo.", "pt-BR-AntonioNeural", output,
                fish_api_key="test-key", session=session, return_provider=True,
            )
            self.assertEqual(audio_path.read_bytes(), b"fish-mp3")
            self.assertEqual(provider, "Fish Audio")
            self.assertFalse(output.with_suffix(".srt").exists())
        args, kwargs = session.calls[0]
        self.assertIn("/v1/tts/stream/with-timestamp", args[0])
        self.assertEqual(kwargs["headers"]["model"], "s2.1-pro-free")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")

    def test_fish_failure_falls_back_to_edge_tts_without_subtitles(self):
        class BrokenFishSession:
            def post(self, *args, **kwargs):
                raise RuntimeError("provider unavailable")
        with tempfile.TemporaryDirectory(prefix="nexus_fish_fallback_") as temp:
            output = Path(temp) / "voice.mp3"
            with patch("nexus.audio.edge_tts.Communicate", FakeCommunicate):
                audio_path, provider = make_voice(
                    "Olá mundo.", "pt-BR-AntonioNeural", output,
                    fish_api_key="test-key", session=BrokenFishSession(),
                    return_provider=True,
                )
            self.assertEqual(audio_path.read_bytes(), b"fake-mp3")
            self.assertTrue(provider.startswith("Edge TTS (fallback:"))
            self.assertFalse(output.with_suffix(".srt").exists())


if __name__ == "__main__":
    unittest.main()
