import pytest

from nexus.cloudflare_images import CloudflareAIError, generate_image


PNG = b"\\x89PNG\\r\\n\\x1a\\n" + b"nexus-test-image"


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


def test_generate_image_saves_png_and_uses_secret_auth(tmp_path):
    session = FakeSession()
    result = generate_image(
        "cinematic portrait, warm light",
        tmp_path / "scene.png",
        account_id="account",
        api_token="secret",
        session=session,
    )
    assert (tmp_path / "scene.png").read_bytes() == PNG
    assert result["model"] == "@cf/black-forest-labs/flux-1-schnell"
    assert session.calls[0][1]["headers"]["Authorization"] == "Bearer secret"
    assert session.calls[0][1]["json"]["steps"] == 6


def test_generate_image_rejects_missing_credentials(tmp_path):
    with pytest.raises(CloudflareAIError, match="CLOUDFLARE_ACCOUNT_ID"):
        generate_image("a scene", tmp_path / "scene.png", account_id="", api_token="")


def test_generate_image_rejects_non_image_payload(tmp_path):
    response = FakeResponse()
    response.content = b"not an image"
    with pytest.raises(CloudflareAIError, match="não é PNG"):
        generate_image(
            "a scene",
            tmp_path / "scene.png",
            account_id="account",
            api_token="secret",
            session=FakeSession(response),
        )


def test_generate_image_rejects_empty_prompt(tmp_path):
    with pytest.raises(ValueError, match="prompt"):
        generate_image(
            " ",
            tmp_path / "scene.png",
            account_id="account",
            api_token="secret",
            session=FakeSession(),
        )
