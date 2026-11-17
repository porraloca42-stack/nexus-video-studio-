import unittest
from unittest.mock import patch

from nexus import director


class NarrationDurationRevisionTests(unittest.TestCase):
    def test_shortens_only_when_measured_voice_exceeds_the_allowed_ceiling(self):
        plan = {
            "scenes": [
                {"voiceover": "A ideia começa aqui.", "visual_action": "Pessoa abre a porta."},
                {"voiceover": "E termina com uma escolha.", "visual_action": "Pessoa segue pela rua."},
            ]
        }
        revised = {
            "scenes": [
                {"scene_number": 1, "voiceover": "A ideia começa aqui e ganha uma explicação concreta."},
                {"scene_number": 2, "voiceover": "E termina com uma escolha consciente e uma ação possível."},
            ]
        }

        with patch.object(director, "_request", return_value=revised) as request:
            result = director.revise_narration_for_duration(
                plan, 60, 66.1, "Tema de teste", "Cinematográfico realista",
                lambda name, default=None: "test-key"
            )

        self.assertIn("explicação concreta", result["scenes"][0]["voiceover"])
        self.assertEqual(len(result["scenes"]), 2)
        self.assertIn("escolha consciente", result["full_narration"])
        self.assertEqual(result["narration_calibration"]["previous_audio_seconds"], 66.1)
        prompt = request.call_args.args[0]
        self.assertIn("66.1 segundos", prompt)
        self.assertIn("velocidade NATURAL", prompt)
        self.assertIn("É PROIBIDO expandir o texto", prompt)
        self.assertIn("encurte SOMENTE", prompt)
        self.assertIn("aproximadamente 8 palavras", prompt)

    def test_rejects_missing_scene_voiceover(self):
        plan = {"scenes": [{"voiceover": "Fala um."}, {"voiceover": "Fala dois."}]}
        with patch.object(director, "_request", return_value={
            "scenes": [{"scene_number": 1, "voiceover": "Fala revisada."}]
        }):
            with self.assertRaisesRegex(RuntimeError, "cada cena"):
                director.revise_narration_for_duration(
                    plan, 60, 66.1, "Tema", "Estilo",
                    lambda name, default=None: "test-key"
                )


if __name__ == "__main__":
    unittest.main()
