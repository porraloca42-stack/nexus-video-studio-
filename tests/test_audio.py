import tempfile
import unittest
from pathlib import Path

from nexus.audio import (
    FishAudioError,
    generate_fish_preview,
    list_fish_voices,
    make_voice,
)


class FakeFishResponse:
    headers = {"content-type": "audio/mpeg"}
    content = b"preview-mp3"

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
    def __init__(self, payload=None):
        self.calls = []
        self.payload = payload or {
            "total": 1,
            "items": [{
                "_id": "voice-123",
                "type": "tts",
                "state": "trained",
                "visibility": "public",
                "title": "Narradora PT",
                "description": "Voz natural para português.",
                "languages": ["pt"],
                "tags": ["female", "narration"],
                "author": {"nickname": "Fish Creator"},
                "samples": [{"audio": "/v1/model/voice-123/sample.mp3", "text": "Olá!"}],
                "task_count": 120,
            }],
        }

    def get(self, *args, **kwargs):
        self.calls.append(("GET", args, kwargs))
        class Response(FakeFishResponse):
            def json(inner_self):
                return self.payload
        return Response()

    def post(self, *args, **kwargs):
        self.calls.append(("POST", args, kwargs))
        return FakeFishResponse()


class AudioOutputTests(unittest.TestCase):
    def test_lists_portuguese_fish_voices_with_preview_sample(self):
        session = FakeFishSession()
        result = list_fish_voices("test-key", page=2, page_size=6, language="pt", session=session)
        self.assertEqual(result["total"], 1)
        voice = result["items"][0]
        self.assertEqual(voice["id"], "voice-123")
        self.assertEqual(voice["title"], "Narradora PT")
        self.assertEqual(voice["sample_audio"], "https://api.fish.audio/v1/model/voice-123/sample.mp3")
        self.assertEqual(session.calls[0][0], "GET")
        self.assertEqual(session.calls[0][2]["params"]["page_number"], 2)
        self.assertEqual(session.calls[0][2]["params"]["language"], "pt")

    def test_generates_short_preview_for_voice_without_public_sample(self):
        session = FakeFishSession()
        audio = generate_fish_preview("test-key", "voice-123", session=session)
        self.assertEqual(audio, b"preview-mp3")
        method, args, kwargs = session.calls[0]
        self.assertEqual(method, "POST")
        self.assertTrue(args[0].endswith("/v1/tts"))
        self.assertEqual(kwargs["json"]["reference_id"], "voice-123")
        self.assertEqual(kwargs["headers"]["model"], "s2.1-pro-free")

    def test_fish_audio_generates_selected_voice_and_reports_provider(self):
        session = FakeFishSession()
        with tempfile.TemporaryDirectory(prefix="nexus_fish_test_") as temp:
            output = Path(temp) / "voice.mp3"
            audio_path, provider = make_voice(
                "Olá mundo.", "voice-123", output,
                fish_api_key="test-key", fish_voice_id="voice-123",
                session=session, return_provider=True,
            )
            self.assertEqual(audio_path.read_bytes(), b"fish-mp3")
            self.assertEqual(provider, "Fish Audio S2.1 Pro Free")
        method, args, kwargs = session.calls[0]
        self.assertEqual(method, "POST")
        self.assertIn("/v1/tts/stream/with-timestamp", args[0])
        self.assertEqual(kwargs["headers"]["model"], "s2.1-pro-free")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(kwargs["json"]["reference_id"], "voice-123")

    def test_narration_requires_fish_credentials_and_never_uses_edge_tts(self):
        with tempfile.TemporaryDirectory(prefix="nexus_fish_required_") as temp:
            output = Path(temp) / "voice.mp3"
            with self.assertRaisesRegex(FishAudioError, "FISH_API_KEY"):
                make_voice("Olá mundo.", "", output)
            with self.assertRaisesRegex(FishAudioError, "Selecione uma voz"):
                make_voice("Olá mundo.", "", output, fish_api_key="test-key")
            self.assertFalse(output.exists())

    def test_fish_failure_is_fatal_and_does_not_silently_fallback(self):
        class BrokenFishSession:
            def post(self, *args, **kwargs):
                raise RuntimeError("provider unavailable")
        with tempfile.TemporaryDirectory(prefix="nexus_fish_failure_") as temp:
            output = Path(temp) / "voice.mp3"
            with self.assertRaisesRegex(FishAudioError, "não substituir a voz"):
                make_voice(
                    "Olá mundo.", "voice-123", output,
                    fish_api_key="test-key", session=BrokenFishSession(),
                )
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
