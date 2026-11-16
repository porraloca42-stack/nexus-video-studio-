import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from nexus.render import render_video


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg/FFprobe not installed")
class RenderIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nexus_render_test_")
        self.root = Path(self.temp.name)
        self.clip_a = self.root / "clip_a.mp4"
        self.clip_b = self.root / "clip_b.mp4"
        self.audio = self.root / "voice.mp3"
        self.subtitles = self.root / "captions.srt"

        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=25",
            "-t", "1.5", "-pix_fmt", "yuv420p", str(self.clip_a)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=teal:size=720x1280:rate=25",
            "-t", "1.5", "-pix_fmt", "yuv420p", str(self.clip_b)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
            "-t", "2.9", "-c:a", "libmp3lame", str(self.audio)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.subtitles.write_text(
            "1\n00:00:00,000 --> 00:00:01,500\nNEXUS render test\n",
            encoding="utf-8"
        )
        self.media = [
            {"path": str(self.clip_a), "duration": 1.5, "camera_motion": "push_in"},
            {"path": str(self.clip_b), "duration": 1.5, "camera_motion": "pan_left"},
        ]

    def tearDown(self):
        self.temp.cleanup()

    def test_render_produces_vertical_mp4_with_audio_and_subtitles(self):
        output = self.root / "result.mp4"
        render_video(self.media, self.audio, output, self.subtitles)

        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration,size:stream=codec_type,codec_name,width,height",
            "-of", "json", str(output)
        ], capture_output=True, text=True, check=True)
        metadata = json.loads(probe.stdout)
        streams = metadata["streams"]
        video = next(item for item in streams if item["codec_type"] == "video")
        audio = next(item for item in streams if item["codec_type"] == "audio")

        self.assertEqual((video["width"], video["height"]), (720, 1280))
        self.assertEqual(video["codec_name"], "h264")
        self.assertEqual(audio["codec_name"], "aac")
        self.assertAlmostEqual(float(metadata["format"]["duration"]), 3.0, delta=0.1)
        self.assertGreater(int(metadata["format"]["size"]), 0)

    def test_large_narration_timing_mismatch_is_rejected(self):
        short_audio = self.root / "short.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100",
            "-t", "1.5", "-c:a", "libmp3lame", str(short_audio)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with self.assertRaisesRegex(RuntimeError, "excede 15%"):
            render_video(self.media, short_audio, self.root / "must_not_render.mp4")


if __name__ == "__main__":
    unittest.main()
