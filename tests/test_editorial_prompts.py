import unittest

from nexus.editorial_prompts import (
    build_edit_timeline_prompt,
    build_hook_strategy_prompt,
    build_micro_script_prompt,
    build_visual_direction_prompt,
)


class EditorialPromptBuilderTests(unittest.TestCase):
    def setUp(self):
        self.brief = {"topic": "A importância de começar"}
        self.hooks = {"selected_hook": "O problema não é falta de tempo."}
        self.script = {"full_narration": "Comece agora.", "blocks": [{"id": "m1", "text": "Comece agora."}]}
        self.visual = {"visual_bible": {"palette": "âmbar"}, "beats": [{"block_id": "m1"}]}
        self.audio = {"audio_asset_id": "voice.wav", "duration_seconds": 4.0}
        self.words = [{"text": "Comece", "start_seconds": 0.0, "end_seconds": 0.5, "confidence": 0.9}]

    def test_each_brain_has_a_separate_specialized_prompt(self):
        prompts = [
            build_hook_strategy_prompt(self.brief),
            build_micro_script_prompt(self.brief, self.hooks),
            build_visual_direction_prompt(self.brief, self.hooks, self.script),
            build_edit_timeline_prompt(self.script, self.visual, self.audio, self.words),
        ]
        self.assertIn("BRAIN 1", prompts[0])
        self.assertIn("BRAIN 2", prompts[1])
        self.assertIn("BRAIN 3", prompts[2])
        self.assertIn("BRAIN 4", prompts[3])
        self.assertEqual(len(set(prompts)), 4)

    def test_micro_script_prompt_keeps_duration_as_heuristic(self):
        prompt = build_micro_script_prompt(self.brief, self.hooks)
        self.assertIn("2,5 e 3,5 segundos", prompt)
        self.assertIn("NÃO um limite rígido", prompt)

    def test_visual_prompt_requires_semantic_metaphor_and_scene_routing(self):
        prompt = build_visual_direction_prompt(self.brief, self.hooks, self.script)
        self.assertIn("metáfora cinematográfica clara", prompt)
        self.assertIn("ai_image_motion", prompt)
        self.assertIn("ai_video", prompt)

    def test_editor_prompt_forbids_invented_phoneme_timing(self):
        prompt = build_edit_timeline_prompt(self.script, self.visual, self.audio, self.words)
        self.assertIn("sincronismo por fonema/sílaba", prompt)
        self.assertIn("NÃO crie timestamps", prompt)
        self.assertIn("word_timestamps", prompt)

    def test_prompt_builder_rejects_non_object_inputs(self):
        with self.assertRaises(TypeError):
            build_hook_strategy_prompt("not a dict")


if __name__ == "__main__":
    unittest.main()
