import unittest
from unittest.mock import patch

from nexus import director


class NarrationDurationRevisionTests(unittest.TestCase):
    def test_shortens_only_when_measured_voice_exceeds_the_allowed_ceiling(self):
        plan = {
            "scenes": [
                {"voiceover": "Você sabe o que precisa fazer, mas continua adiando porque espera sentir confiança antes de dar o primeiro passo.", "visual_action": "Pessoa abre a porta."},
                {"voiceover": "Enquanto isso, os dias passam, a insegurança cresce e o objetivo parece cada vez mais distante, embora nada tenha mudado além da sua decisão de esperar.", "visual_action": "Pessoa segue pela rua."},
            ]
        }
        revised = {
            "scenes": [
                {"scene_number": 1, "voiceover": "Você sabe o que precisa fazer, mas adia o primeiro passo esperando sentir confiança."},
                {"scene_number": 2, "voiceover": "Enquanto espera, os dias passam e o objetivo parece mais distante. A confiança pode surgir depois que você começa, não antes."},
            ]
        }

        with patch.object(director, "_request", return_value=revised) as request:
            result = director.revise_narration_for_duration(
                plan, 60, 66.1, "Tema de teste", "Cinematográfico realista",
                lambda name, default=None: "test-key"
            )

        self.assertIn("adia o primeiro passo", result["scenes"][0]["voiceover"])
        self.assertEqual(len(result["scenes"]), 2)
        self.assertIn("confiança pode surgir", result["full_narration"])
        self.assertEqual(result["narration_calibration"]["previous_audio_seconds"], 66.1)
        prompt = request.call_args.args[0]
        self.assertIn("66.1 segundos", prompt)
        self.assertIn("velocidade NATURAL", prompt)
        self.assertIn("É PROIBIDO expandir o texto", prompt)
        self.assertIn("encurte SOMENTE", prompt)
        self.assertIn("aproximadamente 41 palavras", prompt)

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
