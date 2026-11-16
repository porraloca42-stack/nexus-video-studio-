import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.remote_render_job import generate_worker_narration, _fit_narration_to_timeline


class RemoteNarrationTests(unittest.TestCase):
    def test_worker_passes_fish_credentials_and_requests_provider(self):
        audio = Path("/tmp/nexus-test-narration.mp3")
        with patch("nexus.remote_render_job.make_voice", return_value=(audio, "Fish Audio")) as make:
            result = generate_worker_narration(
                "Texto narrado", "pt-BR-AntonioNeural", audio,
                fish_api_key="fish-key", fish_voice_id="voice-123",
            )
        self.assertEqual(result, (audio, "Fish Audio"))
        self.assertEqual(make.call_args.kwargs["fish_api_key"], "fish-key")
        self.assertEqual(make.call_args.kwargs["fish_voice_id"], "voice-123")
        self.assertTrue(make.call_args.kwargs["return_provider"])

    def test_worker_falls_back_to_edge_when_fish_credentials_absent(self):
        audio = Path("/tmp/nexus-test-narration.mp3")
        with patch("nexus.remote_render_job.make_voice", return_value=(audio, "Edge TTS")) as make:
            result = generate_worker_narration(
                "Texto narrado", "pt-BR-AntonioNeural", audio,
            )
        self.assertEqual(result[1], "Edge TTS")
        self.assertIsNone(make.call_args.kwargs["fish_api_key"])
        self.assertIsNone(make.call_args.kwargs["fish_voice_id"])

    def test_audio_sync_has_no_subtitle_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "voice.mp3"
            audio.write_bytes(b"audio")
            adjusted = audio.with_name("voice_synced.mp3")
            calls = []
            class Result:
                returncode = 0
                stderr = ""
                def __init__(self, stdout=""):
                    self.stdout = stdout
            def run(command, **kwargs):
                calls.append(command)
                if command[0] == "ffprobe":
                    return Result("52.0\n" if len(calls) == 1 else "50.0\n")
                adjusted.write_bytes(b"synced-audio")
                return Result()
            with patch("nexus.remote_render_job.subprocess.run", side_effect=run):
                duration = _fit_narration_to_timeline(audio, 50.0)
            self.assertEqual(duration, 50.0)
            self.assertTrue(audio.exists())
            self.assertFalse(audio.with_suffix(".srt").exists())
            self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
