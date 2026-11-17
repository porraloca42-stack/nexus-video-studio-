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

    def test_director_locks_profile_and_search_terms(self):
        plan = {"scenes": [{"voiceover": "Cena um"}, {"voiceover": "Cena dois"}]}
        result = apply_visual_style_lock(plan, "Quântico & Cósmico")
        self.assertEqual(result["style_lock"], "Quântico & Cósmico")
        self.assertEqual(result["style_profile_version"], "1.0")
        self.assertIn("geometry", result["style_directive"].lower())
        for scene in result["scenes"]:
            self.assertEqual(scene["visual_style"], "Quântico & Cósmico")
            self.assertEqual(scene["style_search_terms"], STYLE_SEARCH_TERMS["Quântico & Cósmico"])


if __name__ == "__main__":
    unittest.main()
