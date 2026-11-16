import io
import json
import unittest
import zipfile

from nexus.github_renderer import render_on_github
from nexus.render_crypto import encrypt_bytes, encrypt_text


class Response:
    def __init__(self, status_code=200, payload=None, content=b"", text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.content = content
        self.text = text

    def json(self):
        return self._payload


class FakeGitHubSession:
    def __init__(self, encryption_secret):
        self.encryption_secret = encryption_secret
        self.calls = []
        self.job_id = None
        self.archive = None

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        self.job_id = kwargs["json"]["inputs"]["job_id"]
        encrypted_manifest = kwargs["json"]["inputs"]["manifest_encrypted"]
        self.assert_no_plaintext(encrypted_manifest)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as bundle:
            bundle.writestr(
                "worker/nexus_video.mp4.enc",
                encrypt_bytes(b"private-mp4", self.encryption_secret),
            )
            bundle.writestr(
                "worker/render-report.json.enc",
                encrypt_text(
                    json.dumps({"duration": 50, "width": 720, "height": 1280}),
                    self.encryption_secret,
                ),
            )
        self.archive = buffer.getvalue()
        return Response(status_code=204)

    def assert_no_plaintext(self, value):
        if "sensitive narration" in value:
            raise AssertionError("Plaintext storyboard leaked into workflow input.")

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if url.endswith("/actions/runs"):
            return Response(payload={"workflow_runs": [{
                "id": 123,
                "display_title": f"NEXUS render {self.job_id}",
            }]})
        if url.endswith("/actions/runs/123"):
            return Response(payload={"status": "completed", "conclusion": "success"})
        if url.endswith("/actions/runs/123/artifacts"):
            return Response(payload={"artifacts": [{
                "id": 456,
                "name": f"nexus-render-{self.job_id}",
            }]})
        if url.endswith("/actions/artifacts/456/zip"):
            return Response(content=self.archive)
        raise AssertionError(f"Unexpected GitHub API URL: {url}")


class GitHubRendererTests(unittest.TestCase):
    def test_dispatches_encrypted_manifest_and_recovers_encrypted_mp4(self):
        secret = "cloudflare-api-token"
        session = FakeGitHubSession(secret)
        result = render_on_github(
            {"scenes": [{"voiceover": "sensitive narration", "duration_seconds": 50}]},
            "pt-BR-AntonioNeural",
            "github-token",
            encryption_secret=secret,
            session=session,
            poll_interval=0,
        )
        self.assertEqual(result["video"], b"private-mp4")
        self.assertEqual(result["report"]["duration"], 50)
        self.assertEqual(result["run_id"], 123)

    def test_requires_encryption_secret(self):
        with self.assertRaisesRegex(RuntimeError, "CLOUDFLARE_API_TOKEN"):
            render_on_github(
                {"scenes": [{"voiceover": "teste", "duration_seconds": 1}]},
                "pt-BR-AntonioNeural",
                "github-token",
            )


if __name__ == "__main__":
    unittest.main()
