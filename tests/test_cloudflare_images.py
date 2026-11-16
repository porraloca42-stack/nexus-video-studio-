import tempfile
import unittest
from pathlib import Path

from nexus.cloudflare_images import CloudflareAIError, generate_image


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


if __name__ == "__main__":
    unittest.main()
