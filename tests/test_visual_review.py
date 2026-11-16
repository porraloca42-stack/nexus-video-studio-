import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nexus.director import review_visual_candidates


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": '{"selected_candidate": 2, "confidence": 91, "reason": "Mostra exatamente a pessoa escrevendo no caderno."}'
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
            payload = post.call_args.kwargs["json"]
            self.assertTrue(any("inlineData" in part for part in payload["contents"][0]["parts"]))

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
