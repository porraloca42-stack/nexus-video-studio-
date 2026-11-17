import unittest

from nexus.render_modes import (
    AI_VIDEO_MODE,
    ECONOMY_MODE,
    RENDER_MODE_OPTIONS,
    default_render_mode,
    mode_uses_modal,
)


class RenderModeTests(unittest.TestCase):
    def test_ai_visuals_are_the_quality_first_default(self):
        self.assertEqual(default_render_mode(), AI_VIDEO_MODE)
        self.assertTrue(mode_uses_modal(default_render_mode()))

    def test_economy_mode_is_an_explicit_lower_cost_option(self):
        self.assertIn(AI_VIDEO_MODE, RENDER_MODE_OPTIONS)
        self.assertTrue(mode_uses_modal(AI_VIDEO_MODE))
        self.assertFalse(mode_uses_modal(ECONOMY_MODE))
        self.assertFalse(mode_uses_modal("unknown"))


if __name__ == "__main__":
    unittest.main()
