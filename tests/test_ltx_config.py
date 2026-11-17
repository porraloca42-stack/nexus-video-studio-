import unittest

from nexus.ltx_config import (
    GPU_RATE_USD_PER_SECOND,
    GPU_COST_BUDGET_USD,
    SCALEDOWN_WINDOW_SECONDS,
    GPU_TYPE,
    FPS,
    IMAGE_COND_NOISE_SCALE,
    INFERENCE_STEP_COUNT,
    MODEL_CHECKPOINT,
    MODEL_CODE_REVISION,
    MODEL_NAME,
    MODEL_REVISION,
    WIDTH,
    HEIGHT,
    PIPELINE_CONFIG,
    SPATIAL_UPSCALER,
    build_pipeline_config,
)


class LTXPipelineConfigTests(unittest.TestCase):
    def test_uses_current_budget_profile_not_legacy_091_single_pass(self):
        self.assertIn("0.9.8", MODEL_NAME)
        self.assertIn("2b-0.9.8-distilled", MODEL_CHECKPOINT)
        self.assertIn("0.9.8", SPATIAL_UPSCALER)
        self.assertEqual(MODEL_REVISION, "main")
        self.assertTrue(MODEL_CODE_REVISION.startswith("50f0aef"))
        self.assertEqual(GPU_TYPE, "L40S")
        self.assertLess(GPU_RATE_USD_PER_SECOND, 0.0006)
        self.assertEqual(GPU_COST_BUDGET_USD, 0.15)
        self.assertEqual(WIDTH, 384)
        self.assertEqual(HEIGHT, 672)
        self.assertEqual(SCALEDOWN_WINDOW_SECONDS, 5)
        self.assertEqual(INFERENCE_STEP_COUNT, 10)
        self.assertEqual(FPS, 24)
        self.assertEqual(IMAGE_COND_NOISE_SCALE, 0.025)

    def test_uses_official_multiscale_7_plus_3_schedule_and_upscaler(self):
        self.assertEqual(PIPELINE_CONFIG["pipeline_type"], "multi-scale")
        self.assertEqual(PIPELINE_CONFIG["downscale_factor"], 0.6666666)
        self.assertEqual(len(PIPELINE_CONFIG["first_pass"]["timesteps"]), 7)
        self.assertEqual(len(PIPELINE_CONFIG["second_pass"]["timesteps"]), 3)
        self.assertEqual(PIPELINE_CONFIG["first_pass"]["guidance_scale"], 1)
        self.assertEqual(PIPELINE_CONFIG["second_pass"]["guidance_scale"], 1)
        self.assertEqual(PIPELINE_CONFIG["prompt_enhancement_words_threshold"], 0)

    def test_build_pipeline_config_returns_independent_copy(self):
        first = build_pipeline_config()
        first["first_pass"]["timesteps"].clear()
        second = build_pipeline_config()
        self.assertEqual(len(second["first_pass"]["timesteps"]), 7)


if __name__ == "__main__":
    unittest.main()
