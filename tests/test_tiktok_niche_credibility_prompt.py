import unittest

from nexus.director import SYSTEM


class TikTokNicheCredibilityPromptTests(unittest.TestCase):
    def test_system_distinguishes_quantum_science_from_metaphor(self):
        self.assertIn("diferencie resultados científicos estabelecidos", SYSTEM)
        self.assertIn("não use partículas", SYSTEM)

    def test_system_avoids_guaranteed_manifestation_claims(self):
        self.assertIn("não prometa manifestação garantida", SYSTEM)
        self.assertIn("favoreça reflexão e ações concretas", SYSTEM)


if __name__ == "__main__":
    unittest.main()
