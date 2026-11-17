import unittest
from unittest.mock import Mock

from nexus.brain4_smoke_test import run_brain4_live_smoke_test


def valid_timeline():
    from nexus.brain4_smoke_test import FIXTURE_AUDIO, FIXTURE_WORD_TIMESTAMPS

    text = " ".join(item["text"] for item in FIXTURE_WORD_TIMESTAMPS)
    return {
        "contract_version": "1.0",
        "audio_asset_id": FIXTURE_AUDIO["audio_asset_id"],
        "alignment_method": FIXTURE_AUDIO["alignment_method"],
        "alignment_level": "word",
        "audio_duration_seconds": FIXTURE_AUDIO["duration_seconds"],
        "word_timestamps": FIXTURE_WORD_TIMESTAMPS,
        "character_timestamps": [],
        "phoneme_timestamps": [],
        "edit_anchors": [{
            "block_id": "scene-01",
            "trigger_text": "visual",
            "at_seconds": 1.0,
            "alignment_level": "word",
            "visual_event": "Change to the second visual beat",
            "sfx": None,
        }],
        "caption_events": [{
            "id": "smoke-caption",
            "start_seconds": 0.0,
            "end_seconds": 3.8,
            "text": text,
            "position": "bottom",
            "words": [
                {**item, "emphasis": False}
                for item in FIXTURE_WORD_TIMESTAMPS
            ],
        }],
        "sfx_events": [],
        "audio_mix_events": [{
            "start_seconds": 0.0,
            "end_seconds": 4.0,
            "music_volume": 0.06,
            "fade_in_seconds": 0.1,
            "fade_out_seconds": 0.1,
        }],
    }


class Brain4SmokeTest(unittest.TestCase):
    def test_live_smoke_test_calls_injected_model_once_and_validates_fixture(self):
        model_call = Mock(return_value=valid_timeline())

        result = run_brain4_live_smoke_test(
            "test-key",
            model_call=model_call,
        )

        self.assertEqual(model_call.call_count, 1)
        self.assertEqual(result["status"], "brain4_validated")
        self.assertEqual(result["alignment_level"], "word")
        self.assertEqual(result["caption_event_count"], 1)
        self.assertEqual(result["audio_mix_event_count"], 1)
        self.assertEqual(result["sfx_event_count"], 0)
        self.assertEqual(result["timeline"]["word_timestamps"], valid_timeline()["word_timestamps"])

    def test_smoke_test_rejects_timestamps_not_matching_fixture(self):
        timeline = valid_timeline()
        timeline["word_timestamps"][0]["start_seconds"] = 0.0
        model_call = Mock(return_value=timeline)

        with self.assertRaisesRegex(ValueError, "does not match a verified provider word timestamp"):
            run_brain4_live_smoke_test("test-key", model_call=model_call)

        self.assertEqual(model_call.call_count, 1)

    def test_live_smoke_test_requires_api_key_before_model_execution(self):
        model_call = Mock(return_value=valid_timeline())
        with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
            run_brain4_live_smoke_test("", model_call=None)
        model_call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
