import unittest
from unittest.mock import patch

from nexus import director


def make_scene(index):
    return {
        "duration_seconds": 4,
        "purpose": f"Beat {index}",
        "voiceover": f"Trecho narrado da cena {index}.",
        "visual_action": f"Uma pessoa realiza uma ação concreta diferente na cena {index}.",
        "image_prompt": f"Opening frame of a person beginning action {index}, hands and relevant props visible, cinematic vertical shot, no text.",
        "video_motion_prompt": f"A person begins action {index}, then performs a clear physical movement with their hands and body. The action progresses naturally and reaches a visible end state in one continuous shot. The camera remains steady.",
        "visual_style": "Cinematográfico realista",
        "style_search_terms": "cinematic realistic natural light",
        "semantic_reason": ("A imagem mostra diretamente a ação descrita na narração, "
                            f"com objeto e ambiente específicos da cena {index}."),
        "setting": f"Ambiente {index}",
        "subjects": f"Pessoa {index}",
        "shot_type": "medium shot",
        "camera_motion": "push_in",
        "motion_events": ["A pessoa inicia a ação", "A câmera acompanha o movimento"],
        "asset_search_query": f"person performing action {index}",
        "fallback_search_query": f"close up detail action {index}",
    }


def make_plan(count):
    scenes = [make_scene(i) for i in range(1, count + 1)]
    return {
        "topic_interpretation": "Teste",
        "creative_thesis": "Teste",
        "hook": "Começo",
        "retention_strategy": "Progressão",
        "cta": "Salve",
        "seo": {"primary_keyword": "teste"},
        "visual_continuity": {"visual_arc": "hesitação para ação", "lead_character": "adult person", "character_reference_prompt": "A realistic cinematic square portrait of the same adult protagonist, neutral pose, simple background, consistent hair and clothing."},
        "full_narration": " ".join(scene["voiceover"] for scene in scenes),
        "scenes": scenes,
    }


class SceneCountRepairTests(unittest.TestCase):
    def test_director_prioritizes_one_observable_action_over_competing_microevents(self):
        self.assertIn("UMA ação principal com progressão visual clara", director.SYSTEM)
        self.assertIn("início → execução → resultado", director.SYSTEM)
        self.assertIn("Não empilhe gestos diferentes", director.SYSTEM)

    def test_automatically_repairs_undersegmented_50_second_storyboard(self):
        short_plan = make_plan(8)
        repaired_plan = make_plan(12)

        def secret_reader(name, default=None):
            return "test-key" if name == "GEMINI_API_KEY" else "auto"

        with patch.object(director, "_request", side_effect=[short_plan, repaired_plan]) as request, \
             patch.object(director, "_repair_semantic_justifications"), \
             patch.object(director, "apply_visual_style_lock", side_effect=lambda plan, style: plan):
            result = director.create_storyboard(
                "Uma manhã tranquila na cidade", "Cinematográfico realista", 50, secret_reader
            )

        self.assertEqual(len(result["scenes"]), 12)
        self.assertEqual(result["requested_duration_seconds"], 50)
        self.assertEqual(result["maximum_duration_seconds"], 60)
        self.assertAlmostEqual(sum(scene["duration_seconds"] for scene in result["scenes"]), result["estimated_duration_seconds"], places=2)
        self.assertEqual(request.call_count, 2)
        self.assertIn("NO MÍNIMO ABSOLUTO 12 CENAS", request.call_args.args[0])

    def test_40_seconds_rejects_seven_and_repairs_to_ten(self):
        short_plan = make_plan(7)
        repaired_plan = make_plan(10)

        def secret_reader(name, default=None):
            return "test-key" if name == "GEMINI_API_KEY" else "auto"

        with patch.object(director, "_request", side_effect=[short_plan, repaired_plan]) as request:
            with patch.object(director, "_repair_semantic_justifications"):
                with patch.object(director, "apply_visual_style_lock", side_effect=lambda plan, style: plan):
                    result = director.create_storyboard(
                        "Uma manhã tranquila na cidade", "Cinematográfico realista", 40, secret_reader
                    )

        self.assertEqual(len(result["scenes"]), 10)
        self.assertEqual(result["maximum_duration_seconds"], 50)
        self.assertAlmostEqual(sum(scene["duration_seconds"] for scene in result["scenes"]), result["estimated_duration_seconds"], places=2)
        self.assertEqual(request.call_count, 2)
        self.assertIn("NO MÍNIMO ABSOLUTO 10 CENAS", request.call_args.args[0])

    def test_validator_rejects_six_or_seven_scenes_even_for_40_seconds(self):
        errors = director.validate_storyboard(make_plan(7), requested_duration=40)
        self.assertTrue(any("pelo menos 10" in error for error in errors))

    def test_keeps_valid_storyboard_without_extra_model_request(self):
        plan = make_plan(12)

        def secret_reader(name, default=None):
            return "test-key" if name == "GEMINI_API_KEY" else "auto"

        with patch.object(director, "_request", return_value=plan) as request, \
             patch.object(director, "_repair_semantic_justifications"), \
             patch.object(director, "apply_visual_style_lock", side_effect=lambda value, style: value):
            result = director.create_storyboard(
                "Uma manhã tranquila na cidade", "Cinematográfico realista", 50, secret_reader
            )

        self.assertEqual(len(result["scenes"]), 12)
        self.assertEqual(request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
