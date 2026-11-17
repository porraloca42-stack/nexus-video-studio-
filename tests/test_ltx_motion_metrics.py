import unittest

from nexus.ltx_motion_metrics import measure_temporal_motion


def blank_frame(size=32):
    return [[[0, 0, 0] for _ in range(size)] for _ in range(size)]


class LtxMotionMetricsTests(unittest.TestCase):
    def test_identical_frames_are_flagged_as_near_static(self):
        frames = [blank_frame() for _ in range(5)]
        result = measure_temporal_motion(frames)
        self.assertTrue(result["near_static_signal"])
        self.assertEqual(result["mean_abs_frame_difference"], 0.0)
        self.assertEqual(result["active_pair_fraction"], 0.0)

    def test_moving_region_is_detected_across_adjacent_frames(self):
        frames = [blank_frame() for _ in range(6)]
        for index, frame in enumerate(frames):
            for y in range(8, 16):
                for x in range(4 + index, 12 + index):
                    frame[y][x] = [255, 255, 255]
        result = measure_temporal_motion(frames)
        self.assertGreater(result["mean_abs_frame_difference"], 0)
        self.assertGreater(result["active_pair_fraction"], 0)
        self.assertFalse(result["near_static_signal"])

    def test_rejects_invalid_frame_shape(self):
        with self.assertRaises(ValueError):
            measure_temporal_motion([blank_frame()])


if __name__ == "__main__":
    unittest.main()
