import unittest
from unittest.mock import patch

from nexus.video_engine import (
    LTX098VideoEngine,
    VideoEngineError,
    get_video_engine,
)


class VideoEngineContractTests(unittest.TestCase):
    def test_default_engine_is_the_existing_ltx098_adapter(self):
        engine = get_video_engine()
        self.assertIsInstance(engine, LTX098VideoEngine)
        self.assertEqual(engine.name, "ltx098")

    def test_ltx098_adapter_preserves_the_existing_worker_contract(self):
        expected = [{"path": "/tmp/scene_01.mp4", "scene_index": 1}]
        with patch("nexus.modal_i2v.animate_scene_images", return_value=expected) as animate:
            result = get_video_engine().animate_scene_images(
                [{"path": "/tmp/keyframe.png"}],
                [{"duration_seconds": 3}],
                "/tmp/output",
                progress_callback=None,
            )
        self.assertIs(result, expected)
        animate.assert_called_once_with(
            [{"path": "/tmp/keyframe.png"}],
            [{"duration_seconds": 3}],
            "/tmp/output",
            progress_callback=None,
        )

    def test_ltx25_is_not_advertised_as_ready_before_workflow_integration(self):
        with self.assertRaisesRegex(VideoEngineError, "workflow API versionado"):
            get_video_engine("ltx25_comfyui")

    def test_unknown_engine_fails_explicitly_without_fallback(self):
        with self.assertRaisesRegex(VideoEngineError, "desconhecido"):
            get_video_engine("other")


if __name__ == "__main__":
    unittest.main()
