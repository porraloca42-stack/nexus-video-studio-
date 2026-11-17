import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.remote_render_job import _fit_narration_to_timeline
from nexus.director import _fit_scene_durations


class RemoteRenderTimingTests(unittest.TestCase):
    def test_scene_timeline_follows_measured_voice_runtime_not_requested_target(self):
        scenes = [
            {"voiceover": "Uma fala curta."},
            {"voiceover": "Esta cena tem uma narração um pouco mais longa, com contexto e conclusão."},
            {"voiceover": "Outra fala de tamanho intermediário para completar a progressão."},
            {"voiceover": "Uma conclusão."},
            {"voiceover": "Uma fala curta."},
            {"voiceover": "Mais uma fala."},
            {"voiceover": "Uma fala de tamanho médio para a narrativa."},
            {"voiceover": "Fechamento."},
            {"voiceover": "Mais contexto."},
            {"voiceover": "CTA final."},
        ]
        durations = _fit_scene_durations(scenes, 35.0)
        self.assertAlmostEqual(sum(durations), 35.0, places=2)
        self.assertTrue(all(1.5 <= value <= 5.0 for value in durations))
        self.assertGreater(durations[1], durations[0])

    def test_adjusts_audio_timing_without_creating_or_retiming_subtitles(self):
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "narration.mp3"
            adjusted = audio.with_name("narration_synced.mp3")
            audio.write_bytes(b"original-audio")
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
            self.assertEqual(audio.read_bytes(), b"synced-audio")
            self.assertFalse(audio.with_suffix(".srt").exists())
            self.assertEqual(len(calls), 3)

    def test_rejects_large_audio_timing_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "narration.mp3"
            audio.write_bytes(b"audio")
            class Result:
                returncode = 0
                stdout = "60.0\n"
            with patch("nexus.remote_render_job.subprocess.run", return_value=Result()):
                with self.assertRaisesRegex(RuntimeError, "excede a faixa segura"):
                    _fit_narration_to_timeline(audio, 50.0)


if __name__ == "__main__":
    unittest.main()
