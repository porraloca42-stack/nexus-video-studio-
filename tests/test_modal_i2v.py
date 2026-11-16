import tempfile
import unittest
from pathlib import Path

from nexus.modal_i2v import ModalVideoError, animate_scene_images, build_motion_prompt


class FakeRemoteMethod:
    def __init__(self, results):
        self.results = results
        self.payload = None

    def remote(self, payload):
        self.payload = payload
        return self.results


class FakeInference:
    def __init__(self, results):
        self.run_batch = FakeRemoteMethod(results)


class FakeModalCls:
    def __init__(self, results):
        self.results = results
        self.app_name = None
        self.class_name = None
        self.instance = FakeInference(results)

    def from_name(self, app_name, class_name):
        self.app_name = app_name
        self.class_name = class_name
        return lambda: self.instance


class ModalI2VTests(unittest.TestCase):
    def test_motion_prompt_prefers_explicit_video_direction(self):
        prompt = build_motion_prompt({
            "video_motion_prompt": "A woman slowly opens a book as sunlight moves across the pages."
        })
        self.assertEqual(prompt, "A woman slowly opens a book as sunlight moves across the pages.")

    def test_motion_prompt_fallback_uses_scene_action_and_camera(self):
        prompt = build_motion_prompt({
            "image_prompt": "Cinematic portrait of a person at a desk.",
            "visual_action": "A pessoa abre o caderno.",
            "camera_motion": "push_in",
            "motion_events": ["the hand turns a page"],
        })
        self.assertIn("Cinematic portrait", prompt)
        self.assertIn("A pessoa abre o caderno", prompt)
        self.assertIn("push in", prompt)
        self.assertIn("the hand turns a page", prompt)

    def test_batch_calls_modal_once_and_saves_every_clip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            images = []
            scenes = []
            for index in range(3):
                path = root / f"scene_{index + 1}.png"
                path.write_bytes(b"image-" + bytes([index]))
                images.append({"path": str(path)})
                scenes.append({
                    "duration_seconds": 3,
                    "image_prompt": "A cinematic scene.",
                    "visual_action": "A person walks naturally.",
                })
            results = [
                {
                    "video_bytes": b"m" * 12000,
                    "duration_seconds": 3.04,
                    "inference_seconds": 9.2,
                    "frames": 73,
                    "model": "Lightricks/LTX-Video",
                }
                for _ in scenes
            ]
            fake_cls = FakeModalCls(results)
            saved = animate_scene_images(images, scenes, root / "clips", modal_cls=fake_cls)
            self.assertEqual(fake_cls.app_name, "nexus-video-i2v")
            self.assertEqual(fake_cls.class_name, "Inference")
            self.assertEqual(len(fake_cls.instance.run_batch.payload), 3)
            self.assertEqual(len(saved), 3)
            self.assertTrue(all(Path(item["path"]).is_file() for item in saved))

    def test_invalid_scene_duration_is_rejected_before_modal_call(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "scene.png"
            image.write_bytes(b"image")
            fake_cls = FakeModalCls([])
            with self.assertRaisesRegex(ModalVideoError, "fora da faixa"):
                animate_scene_images(
                    [{"path": str(image)}],
                    [{"duration_seconds": 8, "image_prompt": "scene"}],
                    root / "clips",
                    modal_cls=fake_cls,
                )
            self.assertIsNone(fake_cls.app_name)


if __name__ == "__main__":
    unittest.main()
