import base64
import tempfile
import unittest
from pathlib import Path

from nexus.cloudflare_images import CloudflareAIError, generate_image, generate_scene_images


PNG = b"\x89PNG\r\n\x1a\n" + b"nexus-test-image"


class FakeResponse:
    status_code = 200
    headers = {"content-type": "image/png"}
    content = PNG
    text = ""

    def json(self):
        return {}


class FakeSession:
    def __init__(self, response=None):
        self.response = response or FakeResponse()
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class CloudflareImageTests(unittest.TestCase):
    def test_generate_image_saves_png_and_uses_secret_auth(self):
        with tempfile.TemporaryDirectory() as temp:
            session = FakeSession()
            result = generate_image(
                "cinematic portrait, warm light",
                Path(temp) / "scene.png",
                account_id="account",
                api_token="secret",
                session=session,
            )
            self.assertEqual((Path(temp) / "scene.png").read_bytes(), PNG)
            self.assertEqual(result["model"], "@cf/black-forest-labs/flux-2-klein-4b")
            self.assertEqual(session.calls[0][1]["headers"]["Authorization"], "Bearer secret")
            self.assertEqual(session.calls[0][1]["files"]["width"], (None, "512"))
            self.assertEqual(session.calls[0][1]["files"]["height"], (None, "910"))
            self.assertEqual(result["steps"], 4)

    def test_generate_image_sends_flux_multi_reference_images(self):
        with tempfile.TemporaryDirectory() as temp:
            session = FakeSession()
            generate_image(
                "Same protagonist opening a notebook in a new room.",
                Path(temp) / "scene.png",
                account_id="account",
                api_token="secret",
                width=512,
                height=910,
                reference_images=[PNG],
                session=session,
            )
            files = session.calls[0][1]["files"]
            self.assertEqual(files["input_image_0"], ("reference_0.png", PNG, "image/png"))
            self.assertEqual(files["prompt"][1].split(".")[0], "Same protagonist opening a notebook in a new room")

    def test_json_base64_jpeg_response_uses_matching_extension(self):
        with tempfile.TemporaryDirectory() as temp:
            jpeg = b"\xff\xd8\xff" + b"nexus-jpeg"
            response = FakeResponse()
            response.headers = {"content-type": "application/json"}
            response.content = b""
            response.json = lambda: {"result": {"image": base64.b64encode(jpeg).decode("ascii")}}
            result = generate_image(
                "portrait scene",
                Path(temp) / "scene.png",
                account_id="account",
                api_token="secret",
                session=FakeSession(response),
            )
            self.assertTrue(result["path"].endswith("scene.jpg"))
            self.assertEqual(Path(result["path"]).read_bytes(), jpeg)

    def test_generate_image_rejects_missing_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(CloudflareAIError, "CLOUDFLARE_ACCOUNT_ID"):
                generate_image("a scene", Path(temp) / "scene.png", account_id="", api_token="")

    def test_generate_image_rejects_non_image_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            response = FakeResponse()
            response.content = b"not an image"
            with self.assertRaisesRegex(CloudflareAIError, "não é PNG"):
                generate_image(
                    "a scene",
                    Path(temp) / "scene.png",
                    account_id="account",
                    api_token="secret",
                    session=FakeSession(response),
                )

    def test_generate_image_rejects_empty_prompt(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "prompt"):
                generate_image(
                    " ",
                    Path(temp) / "scene.png",
                    account_id="account",
                    api_token="secret",
                    session=FakeSession(),
                )


    def test_scene_retries_once_with_safe_framing_after_moderation_3030(self):
        class QueueSession:
            def __init__(self):
                self.calls = []
                self.responses = [
                    type('Blocked', (), {'status_code': 400, 'text': '{"errors":[{"message":"output flagged","code":3030}]}', 'headers': {'content-type': 'application/json'}, 'content': b''})(),
                    FakeResponse(),
                ]

            def post(self, url, **kwargs):
                self.calls.append((url, kwargs))
                return self.responses.pop(0)

        with tempfile.TemporaryDirectory() as temp:
            session = QueueSession()
            result = generate_scene_images(
                [{'image_prompt': 'A fictional traveler walking through a rainy city'}],
                temp, account_id='account', api_token='secret', session=session,
            )
            self.assertEqual(len(session.calls), 2)
            retry_prompt = session.calls[1][1]['files']['prompt'][1]
            self.assertIn('non-graphic, non-sexual', retry_prompt)
            self.assertIn('fictional traveler', retry_prompt)
            self.assertTrue(result[0]['moderation_retry'])
            self.assertEqual(result[0]['scene_index'], 1)

    def test_scene_generation_creates_one_shared_character_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            session = FakeSession()
            scenes = [
                {"image_prompt": "The same person opens a notebook at a desk."},
                {"image_prompt": "The same person stands and walks toward the door."},
            ]
            results = generate_scene_images(
                scenes, temp,
                visual_continuity={
                    "lead_character": "same adult person",
                    "character_reference_prompt": "Square realistic portrait of the same adult person, neutral pose, simple background.",
                },
                account_id="account", api_token="secret", session=session,
            )
            self.assertEqual(len(session.calls), 3)
            self.assertEqual(session.calls[0][1]["files"]["width"], (None, "448"))
            self.assertEqual(session.calls[1][1]["files"]["input_image_0"][1], PNG)
            self.assertEqual(session.calls[2][1]["files"]["input_image_0"][1], PNG)
            self.assertTrue(all(item["continuity_reference_used"] for item in results))

    def test_scene_does_not_retry_non_moderation_cloudflare_errors(self):
        class ErrorSession:
            def __init__(self):
                self.calls = 0
            def post(self, url, **kwargs):
                self.calls += 1
                return type('Failure', (), {'status_code': 500, 'text': 'temporary server error', 'headers': {'content-type': 'application/json'}, 'content': b''})()

        with tempfile.TemporaryDirectory() as temp:
            session = ErrorSession()
            with self.assertRaisesRegex(CloudflareAIError, 'HTTP 500'):
                generate_scene_images([{'image_prompt': 'A quiet city street'}], temp, account_id='account', api_token='secret', session=session)
            self.assertEqual(session.calls, 1)


if __name__ == "__main__":
    unittest.main()
