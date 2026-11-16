import ast
import unittest
from pathlib import Path


class AppImportResilienceTests(unittest.TestCase):
    def test_optional_narration_calibrator_is_not_imported_at_startup(self):
        tree = ast.parse(Path("app.py").read_text(encoding="utf-8"))
        top_level_imports = [
            node for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "nexus.director"
        ]
        imported_names = {
            alias.name
            for node in top_level_imports
            for alias in node.names
        }
        self.assertIn("create_storyboard", imported_names)
        self.assertIn("validate_storyboard", imported_names)
        self.assertNotIn("revise_narration_for_duration", imported_names)

    def test_calibrator_import_is_lazy_and_guarded(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn("from nexus.director import revise_narration_for_duration", source)
        self.assertIn("O módulo do diretor está desatualizado neste servidor.", source)


if __name__ == "__main__":
    unittest.main()
