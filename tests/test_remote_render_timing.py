import tempfile
import unittest
from pathlib import Path

from nexus.remote_render_job import _retime_srt


class RemoteRenderTimingTests(unittest.TestCase):
    def test_retimes_subtitle_cues_with_audio_factor(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "captions.srt"
            target = Path(temp) / "captions_synced.srt"
            source.write_text(
                "1\n00:00:01,000 --> 00:00:02,000\nOlá\n",
                encoding="utf-8",
            )
            _retime_srt(source, target, 0.885)
            result = target.read_text(encoding="utf-8")
            self.assertIn("00:00:01,130 --> 00:00:02,260", result)

    def test_preserves_multiple_subtitle_timestamps(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "captions.srt"
            target = Path(temp) / "captions_synced.srt"
            source.write_text(
                "1\n00:00:10,000 --> 00:00:12,000\nCena\n",
                encoding="utf-8",
            )
            _retime_srt(source, target, 0.90)
            self.assertIn("00:00:11,111 --> 00:00:13,333", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
