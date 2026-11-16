import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.director import review_visual_candidates
from nexus.visual_review import review_scene_frames


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"selected_candidate": 2, "semantic_match": 91, "style_match": 64, "confidence": 91, "reason": "Mostra exatamente a pessoa escrevendo no caderno."}'
                    }]
                }
            }]
        }


class VisualReviewTests(unittest.TestCase):
    def test_gemini_vision_selects_candidate_using_actual_frames(self):
        with tempfile.TemporaryDirectory() as temp:
            frame = Path(temp) / "frame.jpg"
            frame.write_bytes(b"fake-jpeg-frame")
            candidates = [
                {"candidate": {"source": "Pixabay", "title": "Forest"}, "frame_paths": [str(frame)]},
                {"candidate": {"source": "Pexels", "title": "Writing in notebook"}, "frame_paths": [str(frame)]},
            ]
            with patch("nexus.director.discover_models", return_value=["gemini-test"]), patch(
                "nexus.director.requests.post", return_value=FakeResponse()
            ) as post:
                result = review_visual_candidates(
                    {
                        "voiceover": "Anote seus objetivos.",
                        "visual_action": "Pessoa escrevendo em um caderno.",
                        "asset_search_query": "person writing goals in notebook",
                    },
                    candidates,
                    lambda name, default=None: "test-key" if name == "GEMINI_API_KEY" else "auto",
                )

            self.assertEqual(result["selected_candidate"], 2)
            self.assertEqual(result["confidence"], 91)
            self.assertEqual(result["semantic_match"], 91)
            self.assertEqual(result["style_match"], 64)
            payload = post.call_args.kwargs["json"]
            prompt_text = payload["contents"][0]["parts"][0]["text"]
            self.assertIn("Priorize a conexão narrativa útil", prompt_text)
            self.assertIn("Estilo visual é critério secundário", prompt_text)
            self.assertTrue(any("inlineData" in part for part in payload["contents"][0]["parts"]))

    def test_accepts_useful_indirect_visual_metaphor_above_lower_threshold(self):
        response = FakeResponse()
        response.json = lambda: {
            "candidates": [{
                "content": {"parts": [{
                    "text": '{"selected_candidate": 1, "semantic_match": 61, "style_match": 70, "confidence": 61, "reason": "A pessoa organizando o calendário comunica planejamento."}'
                }]}
            }]
        }
        with tempfile.TemporaryDirectory() as temp:
            frame = Path(temp) / "frame.jpg"
            frame.write_bytes(b"fake-jpeg-frame")
            with patch("nexus.director.discover_models", return_value=["gemini-test"]), patch(
                "nexus.director.requests.post", return_value=response
            ):
                result = review_visual_candidates(
                    {"voiceover": "Prepare-se para o que deseja construir.", "visual_action": "Pessoa organizando prioridades."},
                    [{"candidate": {"source": "Pixabay"}, "frame_paths": [str(frame)]}],
                    lambda name, default=None: "test-key" if name == "GEMINI_API_KEY" else "auto",
                )
        self.assertEqual(result["selected_candidate"], 1)
        self.assertEqual(result["confidence"], 61)

    def test_final_review_accepts_three_ordered_frames_per_scene(self):
        response = FakeResponse()
        response.json = lambda: {
            "candidates": [{
                "content": {"parts": [{
                    "text": '{"reviews":[{"scene_number":1,"semantic_score":8,"matches_narration":true,"visual_quality":"Boa sequência","issues":[],"recommendation":"Manter."}]}'
                }]}
            }]
        }
        with tempfile.TemporaryDirectory() as temp:
            paths = []
            for index in range(3):
                frame = Path(temp) / f"frame_{index}.jpg"
                frame.write_bytes(f"frame-{index}".encode())
                paths.append(str(frame))
            from unittest.mock import Mock
            session = Mock()
            session.post.return_value = response
            result = review_scene_frames(
                paths, [{"voiceover":"A pessoa abre a porta.","visual_action":"Pessoa entrando."}],
                "test-key", model="gemini-test", session=session
            )
        self.assertEqual(result[0]["semantic_score"], 8)
        self.assertEqual(len(session.post.call_args.kwargs["json"]["contents"][0]["parts"]), 5)

    def test_final_review_rejects_incomplete_temporal_frame_groups(self):
        with self.assertRaisesRegex(ValueError, "um ou três quadros"):
            review_scene_frames(["one.jpg", "two.jpg"], [{"voiceover":"fala"}], "test-key", model="gemini-test")

    def test_rejects_candidate_below_visual_confidence_threshold(self):
        response = FakeResponse()
        response.json = lambda: {
            "candidates": [{
                "content": {"parts": [{
                    "text": '{"selected_candidate": 1, "confidence": 42, "reason": "Apenas semelhança estética."}'
                }]}
            }]
        }
        with tempfile.TemporaryDirectory() as temp:
            frame = Path(temp) / "frame.jpg"
            frame.write_bytes(b"fake-jpeg-frame")
            with patch("nexus.director.discover_models", return_value=["gemini-test"]), patch(
                "nexus.director.requests.post", return_value=response
            ):
                result = review_visual_candidates(
                    {"voiceover": "Mudar de vida.", "visual_action": "Pessoa tomando uma decisão."},
                    [{"candidate": {"source": "Pixabay"}, "frame_paths": [str(frame)]}],
                    lambda name, default=None: "test-key" if name == "GEMINI_API_KEY" else "auto",
                )

        self.assertEqual(result["selected_candidate"], 0)
        self.assertEqual(result["confidence"], 42)


if __name__ == "__main__":
    unittest.main()
