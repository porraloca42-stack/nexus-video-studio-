import unittest

from nexus.visual_styles import STYLE_OPTIONS, STYLE_PROFILES, STYLE_SEARCH_TERMS, build_visual_style_directive
from nexus.director import apply_visual_style_lock


class VisualStyleLibraryTests(unittest.TestCase):
    def test_catalog_has_exactly_18_curated_styles(self):
        self.assertEqual(len(STYLE_OPTIONS), 18)
        self.assertEqual(set(STYLE_OPTIONS), set(STYLE_PROFILES))

    def test_every_style_has_complete_internal_art_direction(self):
        required = ("short", "search_terms", "palette", "lighting", "camera", "texture", "direction", "avoid", "preview_scene", "ui")
        for name, profile in STYLE_PROFILES.items():
            with self.subTest(style=name):
                self.assertTrue(all(profile.get(key) for key in required))
                brief = build_visual_style_directive(name)
                for section in ("IDENTIDADE E INTENÇÃO:", "PALETA:", "ILUMINAÇÃO:", "FOTOGRAFIA E COMPOSIÇÃO:", "EVITAR:"):
                    self.assertIn(section, brief)

    def test_unknown_style_is_rejected(self):
        with self.assertRaises(ValueError):
            build_visual_style_directive("Estilo inventado")

    def test_hidden_legacy_styles_remain_compatible_but_not_selectable(self):
        self.assertNotIn("Anime 2D", STYLE_OPTIONS)
        self.assertNotIn("Cinematográfico realista", STYLE_OPTIONS)
        self.assertIn("2D anime style", build_visual_style_directive("Anime 2D"))
        self.assertIn("cinematic realistic natural light", build_visual_style_directive("Cinematográfico realista"))

    def test_style_grammar_does_not_encode_fixed_scene_motifs(self):
        forbidden_motifs = (
            "man in front of mirror", "solitary silhouette", "detective",
            "liquid gold", "ancient temple", "floating clocks",
            "espelho", "detetive", "relógio", "templo", "castelo", "gotas",
        )
        for name in STYLE_OPTIONS:
            with self.subTest(style=name):
                profile = STYLE_PROFILES[name]
                terms = profile["search_terms"].lower()
                directive = build_visual_style_directive(name).lower()
                for motif in forbidden_motifs:
                    self.assertNotIn(motif, terms)
                    self.assertNotIn(motif, directive)
                self.assertIn("anti-template", directive)

    def test_full_art_direction_is_attached_to_worker_image_prompt_idempotently(self):
        plan = {
            "scenes": [{
                "voiceover": "Cena",
                "image_prompt": "A person taking a meaningful action in a specific setting",
            }]
        }
        first = apply_visual_style_lock(plan, "Dark Psychology")
        prompt_once = first["scenes"][0]["image_prompt"]
        self.assertIn("NEXUS STYLE DIRECTION:", prompt_once)
        self.assertIn("REGRA ANTI-TEMPLATE", prompt_once)
        second = apply_visual_style_lock(first, "Dark Psychology")
        prompt_twice = second["scenes"][0]["image_prompt"]
        self.assertEqual(prompt_once, prompt_twice)
        self.assertEqual(
            first["scenes"][0]["style_search_terms"],
            second["scenes"][0]["style_search_terms"],
        )

    def test_scene_specific_style_terms_are_preserved_and_formal_terms_appended(self):
        plan = {
            "scenes": [{
                "voiceover": "Cena específica",
                "style_search_terms": "documentary lensing, desaturated color treatment",
            }]
        }
        result = apply_visual_style_lock(plan, "Dark Psychology")
        terms = result["scenes"][0]["style_search_terms"]
        self.assertIn("documentary lensing", terms)
        self.assertIn(STYLE_SEARCH_TERMS["Dark Psychology"], terms)

    def test_director_locks_profile_and_search_terms(self):
        plan = {"scenes": [{"voiceover": "Cena um"}, {"voiceover": "Cena dois"}]}
        result = apply_visual_style_lock(plan, "Quântico & Cósmico")
        self.assertEqual(result["style_lock"], "Quântico & Cósmico")
        self.assertEqual(result["style_profile_version"], "2.0")
        self.assertIn("geometric", result["style_directive"].lower())
        for scene in result["scenes"]:
            self.assertEqual(scene["visual_style"], "Quântico & Cósmico")
            self.assertEqual(scene["style_search_terms"], STYLE_SEARCH_TERMS["Quântico & Cósmico"])


if __name__ == "__main__":
    unittest.main()
