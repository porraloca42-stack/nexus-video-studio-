import tempfile
import unittest
from pathlib import Path

from nexus.audio import (
    FishAudioError,
    generate_fish_preview,
    get_fish_voice,
    list_fish_voices,
    list_fish_professional_narrators,
    _is_natural_brazilian_voice,
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
    def test_list_voices_preserves_license_and_source_metadata(self):
        session = FakeFishSession(payload={
            "total": 1,
            "items": [{
                "_id": "licensed-voice", "type": "tts", "state": "trained",
                "visibility": "public", "title": "Brazilian Studio Narrator",
                "licensed": True, "source": "Fish Audio Marketplace",
                "languages": ["pt"], "samples": [], "task_count": 999,
            }],
        })
        result = list_fish_voices("test-key", language="pt", session=session)
        voice = result["items"][0]
        self.assertTrue(voice["licensed"])
        self.assertEqual(voice["source"], "Fish Audio Marketplace")
        self.assertNotIn("licensed", session.calls[0][2]["params"])

    def test_professional_narrators_are_split_by_gender_and_exclude_characters(self):
        session = FakeFishSession(payload={
            "total": 4,
            "items": [
                {
                    "_id": "male-pvc", "type": "tts", "state": "trained",
                    "visibility": "public", "title": "Brazilian Male Narrator",
                    "description": "Natural Brazilian Portuguese narration",
                    "languages": ["pt"], "tags": ["male", "narration"],
                    "source": "pvc", "task_count": 900,
                    "samples": [{"audio": "https://cdn.example.test/male.mp3"}],
                },
                {
                    "_id": "female-licensed", "type": "tts", "state": "trained",
                    "visibility": "public", "title": "Brazilian Female Narrator",
                    "description": "Warm Brazilian Portuguese narration",
                    "languages": ["pt"], "tags": ["female", "narration"],
                    "source": "licensed", "licensed": True, "task_count": 800,
                    "samples": [{"audio": "https://cdn.example.test/female.mp3"}],
                },
                {
                    "_id": "european-male", "type": "tts", "state": "trained",
                    "visibility": "public", "title": "European Male Narrator",
                    "description": "Professional European Portuguese narration",
                    "languages": ["pt"], "tags": ["male", "narration"],
                    "source": "pvc", "task_count": 1100,
                },
                {
                    "_id": "anime-male", "type": "tts", "state": "trained",
                    "visibility": "public", "title": "Anime Male Character",
                    "description": "Brazilian Portuguese anime character voice",
                    "languages": ["pt"], "tags": ["male", "narration", "anime"],
                    "source": "pvc", "task_count": 1200,
                },
            ],
        })
        voices = list_fish_professional_narrators("test-key", session=session)
        self.assertEqual([voice["id"] for voice in voices["male"]], ["male-pvc"])
        self.assertEqual([voice["id"] for voice in voices["female"]], ["female-licensed"])
        self.assertTrue(voices["female"][0]["licensed"])
        self.assertEqual(len(session.calls), 4)
        queried_tags = {tuple(kwargs["params"]["tag"]) for _, _, kwargs in session.calls}
        self.assertEqual(queried_tags, {("male", "narration"), ("female", "narration")})
        licensed_queries = [kwargs for _, _, kwargs in session.calls if kwargs["params"].get("licensed") == "true"]
        self.assertEqual(len(licensed_queries), 2)

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
        self.assertNotIn("self", session.calls[0][2]["params"])

    def test_gets_one_curated_public_voice_by_stable_id(self):
        session = FakeFishSession(payload={
            "_id": "voice-ricardo",
            "type": "tts",
            "state": "trained",
            "visibility": "public",
            "title": "Ricardo",
            "description": "Brazilian Portuguese male voice",
            "languages": ["pt"],
            "samples": [{"audio": "/sample/ricardo.mp3", "text": "Olá."}],
            "author": {"nickname": "Fish Official"},
        })
        voice = get_fish_voice("test-key", "voice-ricardo", session=session)
        self.assertEqual(voice["id"], "voice-ricardo")
        self.assertEqual(voice["title"], "Ricardo")
        self.assertEqual(voice["sample_audio"], "https://api.fish.audio/sample/ricardo.mp3")
        self.assertEqual(session.calls[0][1][0], "https://api.fish.audio/model/voice-ricardo")

    def test_get_fish_voice_accepts_unlisted_public_model(self):
        session = FakeFishSession(payload={
            "_id": "voice-unlisted", "type": "tts", "state": "trained",
            "visibility": "unlist", "title": "Official Voice",
            "samples": [{"audio": "/sample.mp3", "text": "Olá"}],
        })
        voice = get_fish_voice("test-key", "voice-unlisted", session=session)
        self.assertEqual(voice["id"], "voice-unlisted")
        self.assertEqual(voice["visibility"], "unlist")

    def test_get_fish_voice_rejects_private_models(self):
        session = FakeFishSession(payload={
            "_id": "private-voice", "type": "tts", "state": "trained",
            "visibility": "private", "title": "Private",
        })
        with self.assertRaisesRegex(FishAudioError, "é privada e não está disponível"):
            get_fish_voice("test-key", "private-voice", session=session)

    def test_lists_voice_tags_and_score_sort(self):
        session = FakeFishSession()
        list_fish_voices("test-key", tags=["narration", "conversational"], sort_by="score", session=session)
        params = session.calls[0][2]["params"]
        self.assertEqual(params["tag"], ["narration", "conversational"])
        self.assertEqual(params["sort_by"], "score")

    def test_natural_voice_filter_requires_brazilian_human_narration_and_excludes_characters(self):
        natural = {
            "title": "Narrador Brasileiro Natural",
            "description": "Brazilian Portuguese professional narration, calm and conversational",
            "tags": ["narration", "neutral"],
            "languages": ["pt"],
        }
        character = {
            "title": "Lula Meme",
            "description": "Brazilian Portuguese character voice for memes",
            "tags": ["meme", "character"],
            "languages": ["pt"],
        }
        european = {
            "title": "Narrador Português",
            "description": "Professional narration in European Portuguese",
            "tags": ["narration"],
            "languages": ["pt"],
        }
        self.assertTrue(_is_natural_brazilian_voice(natural))
        self.assertFalse(_is_natural_brazilian_voice(character))
        self.assertFalse(_is_natural_brazilian_voice(european))

    def test_lists_private_personal_voice_models(self):
        session = FakeFishSession(payload={
            "total": 1,
            "items": [{
                "_id": "my-voice",
                "type": "tts",
                "state": "trained",
                "visibility": "private",
                "title": "Minha voz",
                "samples": [{"audio": "https://cdn.example.test/sample.mp3"}],
            }],
        })
        result = list_fish_voices("test-key", self_only=True, session=session)
        self.assertEqual(result["items"][0]["id"], "my-voice")
        self.assertEqual(session.calls[0][2]["params"]["self"], "true")

    def test_generates_short_preview_for_voice_without_public_sample(self):
        session = FakeFishSession()
        audio = generate_fish_preview("test-key", "voice-123", session=session)
        self.assertEqual(audio, b"preview-mp3")
        method, args, kwargs = session.calls[0]
        self.assertEqual(method, "POST")
        self.assertTrue(args[0].endswith("/v1/tts"))
        self.assertEqual(kwargs["json"]["reference_id"], "voice-123")
        self.assertEqual(kwargs["json"]["language"], "pt-BR")
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
        self.assertEqual(kwargs["json"]["language"], "pt-BR")

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
