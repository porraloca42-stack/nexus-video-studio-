import unittest

from nexus.render_modes import (
    AI_VIDEO_MODE,
    ECONOMY_MODE,
    RENDER_MODE_OPTIONS,
    default_render_mode,
    mode_uses_modal,
)


class RenderModeTests(unittest.TestCase):
    def test_economy_mode_is_the_default(self):
        self.assertEqual(default_render_mode(), ECONOMY_MODE)
        self.assertFalse(mode_uses_modal(default_render_mode()))

    def test_modal_requires_explicit_ai_video_mode(self):
        self.assertIn(AI_VIDEO_MODE, RENDER_MODE_OPTIONS)
        self.assertTrue(mode_uses_modal(AI_VIDEO_MODE))
        self.assertFalse(mode_uses_modal(ECONOMY_MODE))
        self.assertFalse(mode_uses_modal("unknown"))


if __name__ == "__main__":
    unittest.main()
