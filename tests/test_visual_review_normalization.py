import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from nexus.visual_review import normalize_review, review_scene_frames


class VisualReviewTests(unittest.TestCase):
    def test_normalize_review_clamps_scores_and_marks_missing_scenes(self):
        scenes = [{"voiceover": "Uma pessoa abre a janela."}, {"voiceover": "A luz entra."}]
        result = normalize_review({"reviews": [
            {"scene_number": 1, "semantic_score": 14, "matches_narration": True,
             "motion_progression_score": 12, "action_observed": True, "continuity_score": -2,
             "temporal_progression": "A mão abre a janela.", "visual_quality": "Boa composição",
             "issues": [], "critical_issues": [], "recommendation": "Manter"},
            {"scene_number": 99, "semantic_score": 8},
        ]}, scenes)
        self.assertEqual(result[0]["semantic_score"], 10)
        self.assertTrue(result[0]["matches_narration"])
        self.assertEqual(result[0]["motion_progression_score"], 10)
        self.assertTrue(result[0]["action_observed"])
        self.assertEqual(result[0]["continuity_score"], 0)
        self.assertEqual(result[0]["temporal_progression"], "A mão abre a janela.")
        self.assertEqual(result[1]["issues"], ["missing_review"])
        self.assertEqual(result[1]["critical_issues"], ["review_missing"])
        self.assertEqual(result[1]["motion_progression_score"], 0)

    def test_normalize_review_rejects_missing_reviews(self):
        with self.assertRaises(ValueError):
            normalize_review({}, [{"voiceover": "fala"}])

    def test_multimodal_request_uses_gemini_inline_data_and_parses_result(self):
        class Response:
            def raise_for_status(self):
                return None
            def json(self):
                return {"candidates": [{"content": {"parts": [{"text":
                    '{"reviews":[{"scene_number":1,"semantic_score":9,"matches_narration":true,'
                    '"visual_quality":"Boa","issues":[],"recommendation":"Manter"}]}'
                }]}}]}
        session = Mock()
        session.post.return_value = Response()
        with tempfile.TemporaryDirectory() as folder:
            frame = Path(folder) / "frame.jpg"
            frame.write_bytes(b"jpeg bytes")
            result = review_scene_frames(
                [frame], [{"voiceover": "A pessoa abre a janela.", "visual_action": "Abrir janela"}],
                "api-key", model="gemini-test", session=session
            )
        self.assertEqual(result[0]["semantic_score"], 9)
        self.assertEqual(result[0]["motion_progression_score"], 8)
        self.assertTrue(result[0]["action_observed"])
        self.assertEqual(result[0]["continuity_score"], 9)
        payload = session.post.call_args.kwargs["json"]
        image_part = payload["contents"][0]["parts"][1]
        self.assertIn("inlineData", image_part)
        self.assertEqual(image_part["inlineData"]["mimeType"], "image/jpeg")


if __name__ == "__main__":
    unittest.main()
