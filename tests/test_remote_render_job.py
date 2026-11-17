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

    def test_worker_requires_fish_credentials_instead_of_using_robotic_fallback(self):
        from nexus.audio import FishAudioError
        audio = Path("/tmp/nexus-test-narration.mp3")
        with self.assertRaisesRegex(FishAudioError, "FISH_API_KEY"):
            generate_worker_narration("Texto narrado", "", audio)


    def test_worker_main_runs_cloudflare_remotion_with_decrypted_fish_credentials(self):
        import json
        import os
        from unittest.mock import Mock, patch
        from nexus.render_crypto import encrypt_compressed_text, encrypt_text, decrypt_text, decrypt_bytes

        with tempfile.TemporaryDirectory(prefix="nexus_remote_worker_") as temp:
            root = Path(temp)
            image_dir = root / "worker_output" / "job-test" / "images"
            image_dir.mkdir(parents=True)
            images = []
            for index in range(1, 11):
                image = image_dir / f"scene_{index:02d}.png"
                image.write_bytes(b"x" * 12000)
                images.append({"path": str(image), "scene_index": index})
            motion_dir = root / "worker_output" / "job-test" / "motion"
            motion_dir.mkdir(parents=True, exist_ok=True)
            clips = []
            for index in range(1, 11):
                clip = motion_dir / f"scene_{index:02d}.mp4"
                clip.write_bytes(b"m" * 12000)
                clips.append({
                    "path": str(clip), "scene_index": index,
                    "duration_seconds": 5.04, "inference_seconds": 15.0,
                    "frames": 121, "model": "Lightricks/LTX-Video",
                })
            audio = root / "worker_output" / "job-test" / "narration.mp3"
            audio.parent.mkdir(parents=True, exist_ok=True)
            audio.write_bytes(b"fish-audio")
            output = root / "worker_output" / "job-test" / "nexus_video.mp4"
            plan = {
                "requested_duration_seconds": 40,
                "maximum_duration_seconds": 50,
                "scenes": [
                    {"duration_seconds": 4, "voiceover": "Uma fala completa.", "image_prompt": "A cinematic portrait."}
                    for _ in range(10)
                ],
            }
            secret = "cloudflare-encryption-secret"
            env = {
                "NEXUS_MANIFEST_ENCRYPTED": encrypt_compressed_text(json.dumps(plan), secret),
                "NEXUS_FISH_CREDENTIALS_ENCRYPTED": encrypt_text(
                    json.dumps({
                        "api_key": "fish-secret", "voice_id": "voice-369",
                        "gemini_api_key": "gemini-secret", "topic": "Tema", "style": "Cinematográfico",
                    }), secret
                ),
                "CLOUDFLARE_API_TOKEN": secret,
                "NEXUS_JOB_ID": "job-test",
                "NEXUS_VOICE": "pt-BR-AntonioNeural",
            }
            image_result = Mock(returncode=0, stdout=json.dumps({"streams": [{"width": 512, "height": 910}]}), stderr="")
            clip_result = Mock(returncode=0, stdout=json.dumps({
                "format": {"duration": 5.04},
                "streams": [{"codec_type": "video", "width": 512, "height": 896}],
            }), stderr="")
            audio_measured = Mock(returncode=0, stdout="37.6\n", stderr="")
            final_result = Mock(returncode=0, stdout=json.dumps({
                "format": {"duration": 37.6, "size": 123456},
                "streams": [
                    {"codec_type": "video", "codec_name": "h264", "width": 720, "height": 1280},
                    {"codec_type": "audio", "codec_name": "aac"},
                ],
            }), stderr="")
            rendered = Mock()
            def fake_render(media, audio_path, destination, plan, **kwargs):
                Path(destination).write_bytes(b"realistic-mocked-mp4")
                return Path(destination)
            def fake_revise_narration(current_plan, target, actual, topic, style, secret_reader):
                self.assertEqual(secret_reader("GEMINI_API_KEY"), "gemini-secret")
                self.assertEqual(secret_reader("GEMINI_MODEL", "auto"), "auto")
                return current_plan
            with patch.dict(os.environ, env, clear=False), \
                 patch("nexus.remote_render_job.generate_scene_images", return_value=images) as gen_images, \
                 patch("nexus.remote_render_job.animate_scene_images", return_value=clips) as animate, \
                 patch("nexus.remote_render_job.generate_worker_narration", return_value=(audio, "Fish Audio")) as gen_voice, \
                 patch("nexus.remote_render_job.revise_narration_for_duration", side_effect=fake_revise_narration) as revise_narration, \
                 patch("nexus.remote_render_job.render_video_remotion", side_effect=fake_render) as render, \
                 patch("nexus.remote_render_job.analyze_video_motion", return_value={
                     "status": "analyzed", "diagnostic": "no_long_freeze_detected",
                     "freeze_ratio": 0.0, "longest_freeze_seconds": 0.0,
                 }), \
                 patch("nexus.remote_render_job.subprocess.run", side_effect=(
                     [audio_measured] + [image_result] * 10 + [clip_result] * 10 + [final_result]
                 )):
                from nexus.remote_render_job import main
                main(project_root=root)

            self.assertEqual(animate.call_args.args[0], images)
            self.assertEqual(len(animate.call_args.args[1]), 10)
            self.assertEqual(gen_voice.call_args.kwargs["fish_api_key"], "fish-secret")
            self.assertEqual(gen_voice.call_args.kwargs["fish_voice_id"], "voice-369")
            self.assertEqual(gen_voice.call_count, 1)
            revise_narration.assert_not_called()
            self.assertAlmostEqual(
                sum(scene["duration_seconds"] for scene in render.call_args.args[3]["scenes"]),
                37.6,
                places=2,
            )
            self.assertEqual(render.call_args.args[3]["actual_duration_seconds"], 37.6)
            self.assertEqual(render.call_args.kwargs, {"project_dir": root / "remotion", "job_id": "job-test"})
            report_path = root / "worker_output" / "job-test" / "render-report.json.enc"
            video_path = root / "worker_output" / "job-test" / "nexus_video.mp4.enc"
            report = json.loads(decrypt_text(report_path.read_text(encoding="ascii"), secret))
            self.assertEqual(report["narration_provider"], "Fish Audio")
            self.assertAlmostEqual(report["duration"], 37.6, places=1)
            self.assertEqual(report["requested_duration"], 40.0)
            self.assertEqual(report["maximum_duration"], 50.0)
            self.assertEqual(report["visual_source"], "Cloudflare FLUX.2 Klein + Modal LTX-Video I2V + Remotion")
            self.assertEqual(len(report["motion_clips"]), 10)
            self.assertEqual(len(report["motion_quality"]), 10)
            self.assertEqual(report["low_motion_scene_count"], 0)
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
