import ast
import unittest
from pathlib import Path


class AppImportResilienceTests(unittest.TestCase):
    def test_credit_sensitive_visual_mode_is_visible_and_quality_first_by_default(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn("render_mode = st.radio(", source)
        self.assertIn('key="nexus_render_mode"', source)
        self.assertIn("if mode_uses_modal(render_mode):", source)
        self.assertIn("Modo de qualidade selecionado", source)
        self.assertIn("Modo Bibliotecas:", source)
        self.assertNotIn('st.selectbox(\n            "Motor de produção visual"', source)

    def test_modal_gpu_estimate_is_carried_to_the_video_result(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn('"estimated_ltx_gpu_cost_usd": report.get("estimated_ltx_gpu_cost_usd")', source)
        self.assertIn("projeção para 22 vídeos", source)
        self.assertIn("somente GPU", source)
        self.assertIn("Não inclui CPU, memória", source)

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

    def test_voice_picker_shows_curated_brazilian_male_and_female_narrators(self):
        source = Path("app.py").read_text(encoding="utf-8")
        start = source.index('@st.dialog("Escolher narração"')
        end = source.index('@st.dialog("Duração do vídeo"', start)
        dialog = source[start:end]
        self.assertIn('catalog_key = "nexus_professional_voice_catalog_v2"', dialog)
        self.assertIn('fish_audio.list_fish_professional_narrators(', dialog)
        self.assertIn('groups = (("Masculinas", "male"), ("Femininas", "female"))', dialog)
        self.assertIn('require_sample=True', dialog)
        self.assertIn('for item in category_voices:', dialog)
        self.assertIn('st.rerun(scope="fragment")', dialog)
        self.assertIn('st.session_state["nexus_pending_voice_id"] = voice_id', dialog)
        self.assertIn('st.session_state["nexus_fish_voice_id"] = pending_id', dialog)
        self.assertIn('st.session_state["nexus_fish_voice_name"] = pending_name', dialog)
        self.assertIn('st.rerun()', dialog)
        self.assertNotIn('CapCut', dialog)
        self.assertNotIn('Adolf Hitler', dialog)
        self.assertNotIn('st.selectbox(', dialog)
        self.assertNotIn('Usar esta voz', dialog)

    def test_voice_picker_uses_published_samples_and_requires_confirmation_without_paid_preview(self):
        source = Path("app.py").read_text(encoding="utf-8")
        start = source.index('@st.dialog("Escolher narração"')
        end = source.index('@st.dialog("Duração do vídeo"', start)
        dialog = source[start:end]
        self.assertIn('key=f"nexus-preview-select-voice-{voice_id}"', dialog)
        self.assertIn('sample_audio = str(item.get("sample_audio") or "")', dialog)
        self.assertIn('st.session_state["nexus_pending_voice_id"] = voice_id', dialog)
        self.assertIn('st.session_state["nexus_pending_voice_preview_source"] = preview_source', dialog)
        self.assertIn('st.audio(pending_source, format="audio/mp3", autoplay=True)', dialog)
        self.assertIn('key="nexus-confirm-pending-voice"', dialog)
        self.assertIn('st.session_state["nexus_fish_voice_id"] = pending_id', dialog)
        self.assertIn('st.session_state["nexus_fish_voice_name"] = pending_name', dialog)
        self.assertNotIn('name_col, play_col = st.columns', dialog)
        self.assertNotIn('nexus_active_voice_preview_id', dialog)
        self.assertNotIn('fish_audio.generate_fish_preview', dialog)
        self.assertIn('uso pessoal não comercial', dialog)
        self.assertIn('O NEXUS não verifica o plano da conta.', dialog)
        self.assertIn('item.get("official_verified")', dialog)

    def test_visual_style_gallery_uses_distinct_visual_language_previews(self):
        source = Path("app.py").read_text(encoding="utf-8")
        preview_start = source.index("def style_preview_svg(style):")
        preview_end = source.index("\nst.markdown(\"\"\"", preview_start)
        preview = source[preview_start:preview_end]
        for style in (
            "Quântico & Cósmico", "Sonho Lúcido", "Dark Psychology",
            "Épico Espiritual", "Aura Neon", "Hermetismo Clássico",
            "Visual ASMR / Hipnótico", "Cinematográfico", "Dark Cinematográfico",
            "Ilustração Editorial", "Filme Noir", "Aquarela Artística",
            "Fantasia Cinematográfica", "Graphic Novel", "Minimalista Clean",
            "Realismo Humano Emocional", "Reconstituição Histórica",
            "Natureza Contemplativa",
        ):
            self.assertIn(f'"{style}":', preview)
        self.assertIn("A visual-language sample, not a scene template", preview)
        self.assertIn("st.image(style_preview_svg(option), use_container_width=True)", source)

    def test_voice_preview_uses_fragment_rerun_without_closing_dialog(self):
        source = Path("app.py").read_text(encoding="utf-8")
        start = source.index('@st.dialog("Escolher narração"')
        end = source.index('@st.dialog("Duração do vídeo"', start)
        dialog = source[start:end]
        self.assertIn('st.rerun(scope="fragment")', dialog)
        self.assertIn('st.session_state["nexus_pending_voice_id"] = voice_id', dialog)
        self.assertNotIn('st.session_state["nexus_pending_voice_name"] = f"{category} · {voice_title}"\n                        st.rerun()', dialog)
        # Confirming is intentionally a full-app rerun so the dialog closes.
        self.assertIn('st.session_state["nexus_fish_voice_id"] = pending_id', dialog)
        self.assertIn('st.session_state.pop(key, None)', dialog)
        self.assertIn('for category, gender in groups:', dialog)

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

    def test_storyboard_preflight_is_exposed_with_clear_limitations(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn('preflight = plan.get("preflight_report")', source)
        self.assertIn('st.markdown("### Pré-validação audiovisual")', source)
        self.assertIn('unique_action_ratio', source)
        self.assertIn('unique_search_ratio', source)
        self.assertIn('unique_shot_types', source)
        self.assertIn('unique_settings', source)
        self.assertIn('action_coverage_ratio', source)
        self.assertIn('motion_prompt_coverage_ratio', source)
        self.assertIn('motion_action_coverage_ratio', source)
        self.assertIn('near_duplicate_action_pairs', source)
        self.assertIn('possíveis pares semelhantes', source)
        self.assertIn('não analisa os quadros', source)
        self.assertIn('Pontos para revisar:', source)
        self.assertIn('Nenhuma repetição literal', source)

    def test_calibrator_import_is_lazy_and_guarded(self):
        source = Path("app.py").read_text(encoding="utf-8")
        self.assertIn("from nexus.director import revise_narration_for_duration", source)
        self.assertIn("O módulo do diretor está desatualizado neste servidor.", source)


if __name__ == "__main__":
    unittest.main()
