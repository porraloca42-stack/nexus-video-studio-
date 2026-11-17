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
        self.assertIn("grid-template-columns:minmax(0,1fr) minmax(0,1fr)", source)
        self.assertIn('max-width:100%!important;min-width:0!important', source)
        self.assertIn('flex:none!important;width:auto!important', source)

    def test_voice_picker_shows_all_provider_groups_and_selects_in_one_tap(self):
        source = Path("app.py").read_text(encoding="utf-8")
        start = source.index('@st.dialog("Escolher narração"')
        end = source.index('@st.dialog("Duração do vídeo"', start)
        dialog = source[start:end]
        self.assertIn('categories = ("CapCut", "ElevenLabs", "Licenciadas Fish")', dialog)
        self.assertIn('total_voices = sum(len(catalog.get(category, [])) for category in categories)', dialog)
        self.assertIn('with st.expander(f"{category} · {len(category_voices)} vozes", expanded=True):', dialog)
        self.assertIn('for row_start in range(0, len(category_voices), 2):', dialog)
        self.assertIn('st.session_state["nexus_fish_voice_id"] = voice_id', dialog)
        self.assertIn('st.session_state["nexus_fish_voice_name"] = f"{category} · {voice_title}"', dialog)
        self.assertIn('st.rerun()', dialog)
        self.assertNotIn('st.selectbox(', dialog)
        self.assertNotIn('Usar esta voz', dialog)

    def test_voice_picker_has_inline_toggle_and_single_shared_audio_player(self):
        source = Path("app.py").read_text(encoding="utf-8")
        start = source.index('@st.dialog("Escolher narração"')
        end = source.index('@st.dialog("Duração do vídeo"', start)
        dialog = source[start:end]
        self.assertIn('name_col, play_col = st.columns([0.86, 0.14]', dialog)
        self.assertIn('"⏸" if is_previewing else "▶"', dialog)
        self.assertIn('if is_previewing:', dialog)
        self.assertIn('st.session_state.pop("nexus_active_voice_preview_source", None)', dialog)
        self.assertIn('st.audio(active_preview_source, format="audio/mp3", autoplay=True)', dialog)
        self.assertIn('fish_audio.generate_fish_preview(api_key, voice_id)', dialog)
        self.assertIn('st.session_state["nexus_active_voice_preview_source"] = preview_source', dialog)
        self.assertNotIn('components.html(', dialog)
        self.assertNotIn('<audio id=', dialog)
        self.assertEqual(dialog.count('st.audio('), 1)

    def test_header_uses_centered_user_supplied_nexus_mark(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn('with st.container(key="nexus-header"):', source)
        self.assertIn('assets" / "nexus-mark.svg', source)
        self.assertIn('NEXUS_MARK_SVG}', source)
        self.assertNotIn('header_left, header_brand, header_settings = st.columns', source)

    def test_duration_dialog_applies_choice_with_one_tap(self):
        source = Path("app.py").read_text(encoding="utf-8")
        start = source.index('@st.dialog("Duração do vídeo"')
        end = source.index('def style_preview_svg', start)
        dialog = source[start:end]
        self.assertIn('for row in ((40, 45), (50, 60)):', dialog)
        self.assertIn('st.session_state["nexus_duration"] = seconds', dialog)
        self.assertNotIn('st.selectbox(', dialog)
        self.assertNotIn('Confirmar duração', dialog)

    def test_calibrator_import_is_lazy_and_guarded(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn("from nexus.director import revise_narration_for_duration", source)
        self.assertIn("O módulo do diretor está desatualizado neste servidor.", source)


if __name__ == "__main__":
    unittest.main()
