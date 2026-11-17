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


    def test_mobile_creation_controls_use_clean_dialogs_and_vertical_stage(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn('@st.dialog("Escolher narração"', source)
        self.assertIn('@st.dialog("Duração do vídeo"', source)
        self.assertIn('key="nexus-open-voice-picker"', source)
        self.assertIn('key="nexus-open-duration-picker"', source)
        self.assertNotIn('with st.popover(f"◷', source)
        self.assertIn("aspect-ratio:9/16", source)

    def test_header_uses_centered_user_supplied_nexus_mark(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn('header_left, header_brand, header_settings = st.columns([1, 4, 1]', source)
        self.assertIn('aria-label="Símbolo N NEXUS"', source)

    def test_calibrator_import_is_lazy_and_guarded(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn("from nexus.director import revise_narration_for_duration", source)
        self.assertIn("O módulo do diretor está desatualizado neste servidor.", source)


if __name__ == "__main__":
    unittest.main()
