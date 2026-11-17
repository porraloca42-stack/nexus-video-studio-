import unittest

from nexus.editorial_executors import build_four_brain_executors, run_brain4_for_storyboard


class EditorialExecutorAdapterTests(unittest.TestCase):
    def test_builders_route_each_stage_to_the_injected_model_call(self):
        prompts = []

        def model_call(prompt):
            prompts.append(prompt)
            return {"stage": len(prompts)}

        executors = build_four_brain_executors(model_call)
        brief = {"topic": "manifestação e hábitos"}
        hook = {"selected_hook": "Comece pelo que controla"}
        script = {"full_narration": "Comece pelo que controla.", "blocks": []}
        visual = {"visual_bible": {"palette": "warm"}, "beats": []}
        audio = {"audio_asset_id": "fish-final.mp3", "duration_seconds": 3.2}
        words = [{"text": "Comece", "start_seconds": 0.0, "end_seconds": 0.4}]

        self.assertEqual(executors["strategist"](brief), {"stage": 1})
        self.assertEqual(
            executors["scriptwriter"]({"brief": brief, "hook_strategy": hook}),
            {"stage": 2},
        )
        self.assertEqual(
            executors["photographer"]({
                "brief": brief, "hook_strategy": hook, "micro_script": script,
            }),
            {"stage": 3},
        )
        self.assertEqual(
            executors["editor"]({
                "micro_script": script,
                "visual_direction": visual,
                "narration_audio": audio,
                "word_timestamps": words,
            }),
            {"stage": 4},
        )

        self.assertEqual(len(prompts), 4)
        self.assertTrue(prompts[0].startswith("BRAIN 1"))
        self.assertTrue(prompts[1].startswith("BRAIN 2"))
        self.assertTrue(prompts[2].startswith("BRAIN 3"))
        self.assertTrue(prompts[3].startswith("BRAIN 4"))
        self.assertIn("Comece", prompts[3])
        self.assertIn("fish-final.mp3", prompts[3])

    def test_brain4_adapter_uses_existing_storyboard_and_verified_audio(self):
        captured = []
        timeline = {
            "contract_version": "1.0",
            "audio_asset_id": "narration.mp3",
            "alignment_method": "Fish Audio timestamp stream",
            "alignment_level": "word",
            "audio_duration_seconds": 4.0,
            "word_timestamps": [
                {"text": "Comece", "start_seconds": 0.0, "end_seconds": 0.4}
            ],
            "character_timestamps": [],
            "phoneme_timestamps": [],
            "edit_anchors": [],
            "caption_events": [],
            "sfx_events": [],
            "audio_mix_events": [],
        }

        def model_call(prompt):
            captured.append(prompt)
            return timeline

        plan = {
            "scenes": [
                {"voiceover": "Comece agora.", "duration_seconds": 4.0, "image_prompt": "A person opening a door."}
            ]
        }
        updated = run_brain4_for_storyboard(
            plan,
            narration_audio={"audio_asset_id": "narration.mp3", "duration_seconds": 4.0},
            word_timestamps=[
                {"text": "Comece", "start_seconds": 0.0, "end_seconds": 0.4}
            ],
            model_call=model_call,
        )
        self.assertEqual(len(captured), 1)
        self.assertTrue(captured[0].startswith("BRAIN 4"))
        self.assertIn("narration.mp3", captured[0])
        self.assertEqual(updated["edit_timeline"], timeline)
        self.assertEqual(updated["editorial_pipeline"]["status"], "brain4_validated")
        self.assertNotIn("edit_timeline", plan)

    def test_brain4_adapter_refuses_unverified_word_timing(self):
        with self.assertRaisesRegex(ValueError, "verified word timestamps"):
            run_brain4_for_storyboard(
                {"scenes": [{"voiceover": "Sem tempos."}]},
                narration_audio={"audio_asset_id": "narration.mp3", "duration_seconds": 1.0},
                word_timestamps=[],
                model_call=lambda prompt: self.fail("model must not be called"),
            )

    def test_factory_requires_an_explicit_model_callable(self):
        with self.assertRaisesRegex(TypeError, "explicitly injected callable"):
            build_four_brain_executors(None)


if __name__ == "__main__":
    unittest.main()
