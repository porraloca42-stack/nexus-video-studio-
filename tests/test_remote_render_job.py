import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.remote_render_job import generate_worker_narration, _fit_narration_to_timeline


class RemoteNarrationTests(unittest.TestCase):
    def test_worker_passes_fish_credentials_and_requests_provider(self):
        audio = Path("/tmp/nexus-test-narration.mp3")
        with patch("nexus.remote_render_job.make_voice", return_value=(audio, "Fish Audio")) as make:
            result = generate_worker_narration(
                "Texto narrado", "pt-BR-AntonioNeural", audio,
                fish_api_key="fish-key", fish_voice_id="voice-123",
            )
        self.assertEqual(result, (audio, "Fish Audio"))
        self.assertEqual(make.call_args.kwargs["fish_api_key"], "fish-key")
        self.assertEqual(make.call_args.kwargs["fish_voice_id"], "voice-123")
        self.assertTrue(make.call_args.kwargs["return_provider"])

    def test_worker_falls_back_to_edge_when_fish_credentials_absent(self):
        audio = Path("/tmp/nexus-test-narration.mp3")
        with patch("nexus.remote_render_job.make_voice", return_value=(audio, "Edge TTS")) as make:
            result = generate_worker_narration(
                "Texto narrado", "pt-BR-AntonioNeural", audio,
            )
        self.assertEqual(result[1], "Edge TTS")
        self.assertIsNone(make.call_args.kwargs["fish_api_key"])
        self.assertIsNone(make.call_args.kwargs["fish_voice_id"])


    def test_worker_main_runs_cloudflare_remotion_with_decrypted_fish_credentials(self):
        import json
        import os
        from unittest.mock import Mock, patch
        from nexus.render_crypto import encrypt_text, decrypt_text, decrypt_bytes

        with tempfile.TemporaryDirectory(prefix="nexus_remote_worker_") as temp:
            root = Path(temp)
            image_dir = root / "worker_output" / "job-test" / "images"
            image_dir.mkdir(parents=True)
            image = image_dir / "scene_01.png"
            image.write_bytes(b"x" * 12000)
            audio = root / "worker_output" / "job-test" / "narration.mp3"
            audio.parent.mkdir(parents=True, exist_ok=True)
            audio.write_bytes(b"fish-audio")
            output = root / "worker_output" / "job-test" / "nexus_video.mp4"
            plan = {"scenes": [{"duration_seconds": 50, "voiceover": "Uma fala completa.", "image_prompt": "A cinematic portrait."}]}
            secret = "cloudflare-encryption-secret"
            env = {
                "NEXUS_MANIFEST_ENCRYPTED": encrypt_text(json.dumps(plan), secret),
                "NEXUS_FISH_CREDENTIALS_ENCRYPTED": encrypt_text(
                    json.dumps({"api_key": "fish-secret", "voice_id": "voice-369"}), secret
                ),
                "CLOUDFLARE_API_TOKEN": secret,
                "NEXUS_JOB_ID": "job-test",
                "NEXUS_VOICE": "pt-BR-AntonioNeural",
            }
            image_result = Mock(returncode=0, stdout=json.dumps({"streams": [{"width": 512, "height": 910}]}), stderr="")
            audio_result = Mock(returncode=0, stdout="50.0\n", stderr="")
            final_result = Mock(returncode=0, stdout=json.dumps({
                "format": {"duration": 50.0, "size": 123456},
                "streams": [
                    {"codec_type": "video", "codec_name": "h264", "width": 720, "height": 1280},
                    {"codec_type": "audio", "codec_name": "aac"},
                ],
            }), stderr="")
            rendered = Mock()
            def fake_render(media, audio_path, destination, plan, **kwargs):
                Path(destination).write_bytes(b"realistic-mocked-mp4")
                return Path(destination)
            with patch.dict(os.environ, env, clear=False), \
                 patch("nexus.remote_render_job.generate_scene_images", return_value=[{"path": str(image), "scene_index": 1}]) as gen_images, \
                 patch("nexus.remote_render_job.generate_worker_narration", return_value=(audio, "Fish Audio")) as gen_voice, \
                 patch("nexus.remote_render_job.render_video_remotion", side_effect=fake_render) as render, \
                 patch("nexus.remote_render_job.subprocess.run", side_effect=[image_result, audio_result, final_result]):
                from nexus.remote_render_job import main
                main(project_root=root)

            self.assertEqual(gen_voice.call_args.kwargs["fish_api_key"], "fish-secret")
            self.assertEqual(gen_voice.call_args.kwargs["fish_voice_id"], "voice-369")
            self.assertEqual(render.call_args.kwargs, {"project_dir": root / "remotion", "job_id": "job-test"})
            report_path = root / "worker_output" / "job-test" / "render-report.json.enc"
            video_path = root / "worker_output" / "job-test" / "nexus_video.mp4.enc"
            report = json.loads(decrypt_text(report_path.read_text(encoding="ascii"), secret))
            self.assertEqual(report["narration_provider"], "Fish Audio")
            self.assertEqual(report["duration"], 50.0)
            self.assertEqual(decrypt_bytes(video_path.read_bytes(), secret), b"realistic-mocked-mp4")

    def test_audio_sync_has_no_subtitle_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "voice.mp3"
            audio.write_bytes(b"audio")
            adjusted = audio.with_name("voice_synced.mp3")
            calls = []
            class Result:
                returncode = 0
                stderr = ""
                def __init__(self, stdout=""):
                    self.stdout = stdout
            def run(command, **kwargs):
                calls.append(command)
                if command[0] == "ffprobe":
                    return Result("52.0\n" if len(calls) == 1 else "50.0\n")
                adjusted.write_bytes(b"synced-audio")
                return Result()
            with patch("nexus.remote_render_job.subprocess.run", side_effect=run):
                duration = _fit_narration_to_timeline(audio, 50.0)
            self.assertEqual(duration, 50.0)
            self.assertTrue(audio.exists())
            self.assertFalse(audio.with_suffix(".srt").exists())
            self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
