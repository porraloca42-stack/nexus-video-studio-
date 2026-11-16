import unittest

from nexus.director import SYSTEM


class ProfessionalDirectorBriefTests(unittest.TestCase):
    def test_director_system_requires_professional_hook_retention_cta_and_semantic_seo(self):
        for requirement in (
            "HOOK:",
            "RETENÇÃO:",
            "NARRAÇÃO:",
            "PONTUAÇÃO PARA INTERPRETAÇÃO VOCAL:",
            "Leia mentalmente cada frase em voz alta.",
            "Varie o comprimento das frases",
            "Preserve pontuação e segmentação expressiva",
            "CTA:",
            "SEO SEMÂNTICO:",
            "keyword stuffing",
            "público provável",
            "primeira fala",
        ):
            with self.subTest(requirement=requirement):
                self.assertIn(requirement, SYSTEM)

    def test_output_contract_includes_editorial_and_seo_metadata(self):
        for field in (
            '"hook"',
            '"retention_strategy"',
            '"cta"',
            '"seo"',
            '"primary_keyword"',
            '"secondary_keywords"',
            '"description"',
            '"hashtags"',
        ):
            with self.subTest(field=field):
                self.assertIn(field, SYSTEM)


if __name__ == "__main__":
    unittest.main()
