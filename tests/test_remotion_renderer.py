import json
import tempfile
import unittest
from pathlib import Path

from nexus.remotion_renderer import build_remotion_manifest
from nexus.editorial_executors import run_brain4_for_storyboard


class RemotionManifestTests(unittest.TestCase):
    def test_builds_manifest_and_copies_video_audio(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            public = root / "public"
            clip = root / "clip.mp4"
            audio = root / "voice.mp3"
            clip.write_bytes(b"fake-video")
            audio.write_bytes(b"fake-audio")
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
            self.assertEqual(direction["camera"]["endScale"], 1.18)
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

    def test_still_scene_without_camera_direction_defaults_to_static_not_fake_zoom(self):
        from nexus.remotion_renderer import sanitize_scene_direction
        direction = sanitize_scene_direction({})
        self.assertEqual(direction["camera"]["move"], "static")
        self.assertEqual(direction["camera"]["startScale"], 1.0)
        self.assertEqual(direction["camera"]["endScale"], 1.0)
        self.assertEqual(direction["camera"]["intensity"], 0.45)

    def test_explicit_push_in_uses_subtle_bounded_motion(self):
        from nexus.remotion_renderer import sanitize_scene_direction
        direction = sanitize_scene_direction({"camera": {"move": "push_in"}})
        self.assertEqual(direction["camera"]["move"], "push_in")
        self.assertEqual(direction["camera"]["startScale"], 1.0)
        self.assertEqual(direction["camera"]["endScale"], 1.08)

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
            path, manifest = build_remotion_manifest(plan, [], None, Path(temp), job_id="graphic")
            self.assertEqual(manifest["scenes"][0]["visualMode"], "graphic")
            self.assertIsNone(manifest["scenes"][0]["asset"])
            self.assertEqual(manifest["durationInFrames"], 90)
            self.assertTrue(path.is_file())


    def test_manifest_copies_and_maps_captions_sfx_music_and_ducking(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            voice = root / "voice.wav"
            music = root / "music.mp3"
            sfx = root / "whoosh.wav"
            voice.write_bytes(b"voice")
            music.write_bytes(b"music")
            sfx.write_bytes(b"sound-effect")
            plan = {
                "music_audio_path": str(music),
                "music_volume": 0.12,
                "scenes": [{"duration_seconds": 4, "voiceover": "O problema começa aqui."}],
                "edit_timeline": {
                    "caption_events": [{
                        "id": "cap-1", "start_seconds": 0, "end_seconds": 2,
                        "text": "O problema", "position": "bottom",
                        "words": [
                            {"text": "O", "start_seconds": 0, "end_seconds": 0.2},
                            {"text": "problema", "start_seconds": 0.21, "end_seconds": 0.9, "emphasis": True},
                        ],
                    }],
                    "sfx_events": [{
                        "id": "sfx-1", "asset_path": str(sfx),
                        "start_seconds": 1.0, "duration_seconds": 0.6, "volume": 0.3,
                    }],
                    "audio_mix_events": [{
                        "start_seconds": 0, "end_seconds": 2.5, "music_volume": 0.04,
                        "fade_in_seconds": 0.2, "fade_out_seconds": 0.3,
                    }],
                },
            }
            _, manifest = build_remotion_manifest(
                plan, [], voice, root / "public", job_id="timeline"
            )
            self.assertEqual(manifest["musicAudio"], "jobs/timeline/music.mp3")
            self.assertEqual(manifest["captionEvents"][0]["words"][1]["emphasis"], True)
            self.assertEqual(manifest["soundEffects"][0]["asset"], "jobs/timeline/sfx_01.wav")
            self.assertEqual(manifest["audioMixEvents"][0]["musicVolume"], 0.04)
            self.assertEqual(manifest["audioMixEvents"][0]["fadeInSeconds"], 0.2)
            self.assertEqual(manifest["audioMixEvents"][0]["fadeOutSeconds"], 0.3)
            self.assertTrue((root / "public/jobs/timeline/sfx_01.wav").is_file())
            self.assertTrue((root / "public/jobs/timeline/music.mp3").is_file())

    def test_brain4_validated_timeline_flows_into_remotion_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            voice = root / "voice.wav"
            music = root / "music.mp3"
            sfx = root / "whoosh.wav"
            voice.write_bytes(b"voice")
            music.write_bytes(b"music")
            sfx.write_bytes(b"sound-effect")
            source_words = [
                {"text": "Comece", "start_seconds": 0.0, "end_seconds": 0.4}
            ]
            timeline = {
                "contract_version": "1.0",
                "audio_asset_id": str(voice),
                "alignment_method": "Fish Audio timestamp stream",
                "alignment_level": "word",
                "audio_duration_seconds": 4.0,
                "word_timestamps": source_words,
                "character_timestamps": [],
                "phoneme_timestamps": [],
                "edit_anchors": [],
                "caption_events": [{
                    "id": "caption-1", "start_seconds": 0.0, "end_seconds": 1.0,
                    "text": "Comece", "position": "bottom",
                    "words": [{
                        "text": "Comece", "start_seconds": 0.0,
                        "end_seconds": 0.4, "emphasis": True,
                    }],
                }],
                "sfx_events": [{
                    "id": "sfx-1", "asset_path": str(sfx),
                    "start_seconds": 0.8, "duration_seconds": 0.5, "volume": 0.2,
                }],
                "audio_mix_events": [{
                    "start_seconds": 0.0, "end_seconds": 4.0,
                    "music_volume": 0.04, "fade_in_seconds": 0.2,
                    "fade_out_seconds": 0.3,
                }],
            }
            plan = {
                "music_audio_path": str(music),
                "scenes": [{
                    "duration_seconds": 4.0,
                    "voiceover": "Comece agora.",
                    "image_prompt": "A person opening a door.",
                }],
            }
            updated = run_brain4_for_storyboard(
                plan,
                narration_audio={"audio_asset_id": str(voice), "duration_seconds": 4.0},
                word_timestamps=source_words,
                model_call=lambda prompt: timeline,
            )
            _, manifest = build_remotion_manifest(
                updated, [], voice, root / "public", job_id="brain4-integration"
            )
            self.assertEqual(len(manifest["captionEvents"]), 1)
            self.assertEqual(manifest["captionEvents"][0]["words"][0]["endSeconds"], 0.4)
            self.assertEqual(len(manifest["soundEffects"]), 1)
            self.assertEqual(manifest["audioMixEvents"][0]["musicVolume"], 0.04)
            self.assertEqual(manifest["audioMixEvents"][0]["fadeOutSeconds"], 0.3)

    def test_manifest_rejects_caption_word_outside_caption_interval(self):
        with tempfile.TemporaryDirectory() as temp:
            plan = {
                "scenes": [{"duration_seconds": 3, "voiceover": "Teste."}],
                "edit_timeline": {
                    "caption_events": [{
                        "id": "cap-1", "start_seconds": 0, "end_seconds": 1,
                        "text": "Teste", "words": [
                            {"text": "Teste", "start_seconds": 0.2, "end_seconds": 1.5},
                        ],
                    }],
                },
            }
            with self.assertRaisesRegex(ValueError, "Palavra temporizada fora"):
                build_remotion_manifest(plan, [], None, Path(temp), job_id="bad-caption")

    def test_invalid_duration_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                build_remotion_manifest(
                    {"scenes": [{"duration_seconds": 0}]}, [], None,
                    Path(temp), job_id="invalid"
                )



if __name__ == "__main__":
    unittest.main()
