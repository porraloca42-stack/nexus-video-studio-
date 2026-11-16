import json
import tempfile
import unittest
from pathlib import Path

from nexus.remotion_renderer import build_remotion_manifest


class RemotionManifestTests(unittest.TestCase):
    def test_builds_manifest_and_copies_video_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            public = root / "public"
            clip = root / "clip.mp4"
            audio = root / "voice.mp3"
            clip.write_bytes(b"fake-video")
            audio.write_bytes(b"fake-audio")
            srt.write_text(
                "1\n00:00:00,000 --> 00:00:02,000\nPrimeira frase.\n",
                encoding="utf-8",
            )
            plan = {
                "seo": {"title": "Teste NEXUS"},
                "scenes": [{
                    "id": "s1", "duration_seconds": 2,
                    "voiceover": "Primeira frase.",
                    "visual_action": "Pessoa abre uma porta.",
                }],
            }
            manifest_path, manifest = build_remotion_manifest(
                plan, [{"path": str(clip)}], audio, public, job_id="test"
            )
            self.assertTrue(manifest_path.is_file())
            self.assertEqual(manifest["durationInFrames"], 60)
            self.assertEqual(manifest["scenes"][0]["visualMode"], "video")
            self.assertNotIn("captions", manifest)
            self.assertTrue((public / "jobs/test/scene_01.mp4").is_file())
            self.assertTrue((public / "jobs/test/narration.mp3").is_file())
            self.assertEqual(json.loads(manifest_path.read_text())["title"], "Teste NEXUS")

    def test_manifest_keeps_director_metadata_off_screen_and_passes_motion_events(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "scene.png"
            image.write_bytes(b"fake-image")
            plan = {"scenes": [{
                "duration_seconds": 4,
                "voiceover": "A pessoa abre a janela.",
                "visual_action": "Pessoa abre uma janela ao amanhecer.",
                "image_prompt": "A person opening a window at sunrise.",
                "motion_events": ["A mão alcança a maçaneta", "A janela se abre"],
                "camera_motion": "push_in",
            }]}
            _, manifest = build_remotion_manifest(
                plan, [{"path": str(image)}], None, root / "public", job_id="motion"
            )
            scene = manifest["scenes"][0]
            self.assertEqual(scene["motionEvents"], ["A mão alcança a maçaneta", "A janela se abre"])
            self.assertNotIn("visualDescription", scene)
            self.assertNotIn("headline", scene)

    def test_scene_direction_is_whitelisted_clamped_and_passed_to_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "scene.png"
            image.write_bytes(b"fake-image")
            plan = {"scenes": [{
                "duration_seconds": 4, "camera_motion": "push_in",
                "scene_direction": {
                    "camera": {"move": "tilt_up", "intensity": 9, "start_scale": 0.2, "end_scale": 2, "focus": "invalid"},
                    "depth_layers": {"parallax_strength": -4},
                    "lighting": {"change": "run arbitrary code"},
                    "atmosphere": {"effect": "explosion", "intensity": 4},
                    "transition": {"in": "crossfade", "out": "unknown", "duration_frames": 90},
                    "beats": [{"at": 3, "event": "A luz pulsa", "visual_target": "fundo"}] * 5,
                },
            }]}
            _, manifest = build_remotion_manifest(plan, [{"path": str(image)}], None, root / "public", job_id="direction")
            direction = manifest["scenes"][0]["sceneDirection"]
            self.assertEqual(direction["camera"]["move"], "tilt_up")
            self.assertEqual(direction["camera"]["intensity"], 1.0)
            self.assertEqual(direction["camera"]["startScale"], 1.0)
            self.assertEqual(direction["camera"]["endScale"], 1.15)
            self.assertEqual(direction["camera"]["focus"], "subject")
            self.assertEqual(direction["depthLayers"]["parallaxStrength"], 0.0)
            self.assertEqual(direction["lighting"]["change"], "none")
            self.assertEqual(direction["atmosphere"]["effect"], "none")
            self.assertEqual(direction["atmosphere"]["intensity"], 1.0)
            self.assertEqual(direction["transition"]["in"], "crossfade")
            self.assertEqual(direction["transition"]["out"], "cut")
            self.assertEqual(direction["transition"]["durationFrames"], 12)
            self.assertEqual(len(direction["beats"]), 3)
            self.assertEqual(direction["beats"][0]["at"], 1.0)

    def test_preserves_wav_extension_for_generated_narration(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            audio = root / "voice.wav"
            audio.write_bytes(b"fake-wav")
            plan = {"scenes": [{"duration_seconds": 2, "voiceover": "Teste."}]}
            _, manifest = build_remotion_manifest(
                plan, [], audio, root / "public", job_id="wav"
            )
            self.assertEqual(manifest["narrationAudio"], "jobs/wav/narration.wav")
            self.assertTrue((root / "public/jobs/wav/narration.wav").is_file())

    def test_graphic_scene_without_stock_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            plan = {"scenes": [{"duration_seconds": 3, "voiceover": "Ideia."}]}
            path, manifest = build_remotion_manifest(plan, [], None, None, Path(temp), job_id="graphic")
            self.assertEqual(manifest["scenes"][0]["visualMode"], "graphic")
            self.assertIsNone(manifest["scenes"][0]["asset"])
            self.assertEqual(manifest["durationInFrames"], 90)
            self.assertTrue(path.is_file())

    def test_invalid_duration_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                build_remotion_manifest(
                    {"scenes": [{"duration_seconds": 0}]}, [], None, None,
                    Path(temp), job_id="invalid"
                )

    def test_parse_srt_captions(self):
        with tempfile.TemporaryDirectory() as temp:
            srt = Path(temp) / "captions.srt"
            srt.write_text(
                "1\n00:00:01,000 --> 00:00:02,500\nUma legenda\ncom duas linhas\n",
                encoding="utf-8",
            )
            captions = parse_srt_captions(srt, fps=30)
            self.assertEqual(captions, [{
                "text": "Uma legenda com duas linhas",
                "startFrame": 30,
                "endFrame": 75,
            }])


if __name__ == "__main__":
    unittest.main()
