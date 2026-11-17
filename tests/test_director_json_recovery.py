import json
import unittest
from unittest.mock import patch

from nexus import director


class FakeResponse:
    def __init__(self, text, finish_reason="STOP", status_code=200):
        self.status_code = status_code
        self.ok = status_code == 200
        self._text = text
        self._finish_reason = finish_reason

    def json(self):
        return {
            "candidates": [{
                "finishReason": self._finish_reason,
                "content": {"parts": [{"text": self._text}]},
            }]
        }


class GeminiJsonRecoveryTests(unittest.TestCase):
    def test_brain4_gemini_call_is_single_request_and_accepts_timeline_contract(self):
        timeline = {
            "contract_version": "1.0",
            "audio_asset_id": "narration.mp3",
            "alignment_method": "Fish Audio",
            "alignment_level": "word",
            "audio_duration_seconds": 4.0,
            "word_timestamps": [],
            "character_timestamps": [],
            "phoneme_timestamps": [],
            "edit_anchors": [],
            "caption_events": [],
            "sfx_events": [],
            "audio_mix_events": [],
        }
        with patch.object(director, "discover_models", return_value=["gemini-flash-test"]) as discover, \
             patch.object(
                 director.requests, "post",
                 return_value=FakeResponse(json.dumps(timeline)),
             ) as post:
            result = director.generate_editorial_json(
                "BRAIN 4 prompt", "private-test-key", "gemini-flash-test"
            )

        self.assertEqual(result, timeline)
        discover.assert_called_once_with("private-test-key", "gemini-flash-test")
        self.assertEqual(post.call_count, 1)
        payload = post.call_args.kwargs["json"]
        self.assertIn("Brain 4", payload["systemInstruction"]["parts"][0]["text"])
        self.assertEqual(
            payload["contents"][0]["parts"][0]["text"], "BRAIN 4 prompt"
        )

    def test_retries_malformed_json_then_fails_over_to_next_model(self):
        valid_plan = {
            "topic_interpretation": "Tema interpretado",
            "creative_thesis": "Tese",
            "style_lock": "Cinematográfico realista",
            "full_narration": "Uma fala.",
            "scenes": [{
                "duration_seconds": 4,
                "voiceover": "Uma fala.",
                "visual_action": "Uma ação concreta.",
            }],
        }
        responses = [
            FakeResponse('{"topic_interpretation":"incompleto",'),
            FakeResponse('{"topic_interpretation":"ainda incompleto",'),
            FakeResponse(json.dumps(valid_plan, ensure_ascii=False)),
        ]

        def secret_reader(name, default=None):
            return "test-key" if name == "GEMINI_API_KEY" else "auto"

        with patch.object(director, "discover_models", return_value=["gemini-flash-a", "gemini-flash-b"]), \
             patch.object(director.requests, "post", side_effect=responses) as post:
            result = director._request("Crie um roteiro de teste.", secret_reader)

        self.assertEqual(result["scenes"][0]["voiceover"], "Uma fala.")
        self.assertEqual(result["director_model"], "gemini-flash-b")
        self.assertEqual(post.call_count, 3)
        retry_payload = post.call_args_list[1].kwargs["json"]
        self.assertIn("RETRY OBRIGATÓRIO", retry_payload["contents"][0]["parts"][0]["text"])
        self.assertEqual(
            post.call_args_list[2].kwargs["json"]["contents"][0]["parts"][0]["text"],
            "Crie um roteiro de teste.",
        )


if __name__ == "__main__":
    unittest.main()
