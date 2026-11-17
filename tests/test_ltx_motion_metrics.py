import unittest

import numpy as np

from nexus.ltx_motion_metrics import measure_temporal_motion


class LtxMotionMetricsTests(unittest.TestCase):
    def test_identical_frames_are_flagged_as_near_static(self):
        frames = np.zeros((5, 32, 32, 3), dtype=np.uint8)
        result = measure_temporal_motion(frames)
        self.assertTrue(result["near_static_signal"])
        self.assertEqual(result["mean_abs_frame_difference"], 0.0)
        self.assertEqual(result["active_pair_fraction"], 0.0)

    def test_moving_region_is_detected_across_adjacent_frames(self):
        frames = np.zeros((6, 32, 32, 3), dtype=np.uint8)
        for index in range(6):
            frames[index, 8:16, 4 + index:12 + index, :] = 255
        result = measure_temporal_motion(frames)
        self.assertGreater(result["mean_abs_frame_difference"], 0)
        self.assertGreater(result["active_pair_fraction"], 0)
        self.assertFalse(result["near_static_signal"])

    def test_rejects_invalid_frame_shape(self):
        with self.assertRaises(ValueError):
            measure_temporal_motion(np.zeros((1, 32, 32, 3), dtype=np.uint8))


if __name__ == "__main__":
    unittest.main()
