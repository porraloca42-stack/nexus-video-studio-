import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.video_quality import analyze_video_motion, parse_freeze_intervals


class VideoQualityTests(unittest.TestCase):
    def test_parses_closed_and_end_of_file_freeze_intervals(self):
        report = parse_freeze_intervals(
            "[freezedetect] lavfi.freezedetect.freeze_start: 0.0\\n"
            "[freezedetect] lavfi.freezedetect.freeze_end: 1.5\\n"
            "[freezedetect] lavfi.freezedetect.freeze_duration: 1.5\\n"
            "[freezedetect] lavfi.freezedetect.freeze_start: 2.5\\n",
            4.0,
        )
        self.assertEqual(report["frozen_seconds"], 3.0)
        self.assertEqual(report["freeze_ratio"], 0.75)
        self.assertEqual(report["longest_freeze_seconds"], 1.5)
        self.assertEqual(report["diagnostic"], "low_motion_warning")

    def test_no_freeze_events_produces_no_long_freeze_warning(self):
        report = parse_freeze_intervals("FFmpeg completed", 3.0)
        self.assertEqual(report["frozen_seconds"], 0.0)
        self.assertEqual(report["freeze_ratio"], 0.0)
        self.assertEqual(report["diagnostic"], "no_long_freeze_detected")

    def test_freeze_ratio_is_bounded_to_clip_duration(self):
        report = parse_freeze_intervals(
            "lavfi.freezedetect.freeze_start: 1.0",
            2.0,
        )
        self.assertEqual(report["frozen_seconds"], 1.0)
        self.assertEqual(report["freeze_ratio"], 0.5)

    def test_runs_ffmpeg_without_external_service(self):
        with tempfile.TemporaryDirectory() as temp:
            clip = Path(temp) / "clip.mp4"
            clip.write_bytes(b"video")
            completed = type("Completed", (), {
                "returncode": 0,
                "stderr": "lavfi.freezedetect.freeze_start: 0.0",
            })()
            with patch("nexus.video_quality.subprocess.run", return_value=completed) as run:
                report = analyze_video_motion(clip, 2.0)
            self.assertEqual(report["freeze_ratio"], 1.0)
            self.assertEqual(run.call_args.args[0][0], "ffmpeg")


if __name__ == "__main__":
    unittest.main()
