import unittest

from nexus.editorial_pipeline import (
    CONTRACT_VERSION,
    editorial_pipeline_is_valid,
    validate_edit_timeline,
    validate_hook_strategy,
    validate_micro_script,
    validate_visual_direction,
    micro_script_advisories,
    run_four_brain_pipeline,
)


def valid_hook_strategy():
    return {
        "contract_version": CONTRACT_VERSION,
        "hook_candidates": [
            {"type": "curiosity", "text": "Por que isso acontece?", "rationale": "Abre uma pergunta específica."},
            {"type": "loss_opportunity", "text": "Você pode estar ignorando este sinal.", "rationale": "Aponta uma oportunidade real."},
            {"type": "pattern_break", "text": "O problema não é falta de tempo.", "rationale": "Contraria uma suposição comum."},
        ],
        "selected_hook_type": "pattern_break",
        "selected_hook": "O problema não é falta de tempo.",
        "selection_reason": "É específico e prepara a tese do vídeo.",
        "narrative_promise": "Explicar o que mantém o ciclo de adiamento.",
        "payoff": "Um primeiro passo pequeno reduz a barreira de começar.",
        "ending_loop_bridge": "A pergunta inicial ganha novo sentido após a explicação.",
        "narrative_beats": [
            {"id": "b1", "purpose": "Abrir a tensão", "tension_level": 2, "expected_payoff": "Reformular o problema"},
            {"id": "b2", "purpose": "Entregar a solução", "tension_level": 4, "expected_payoff": "Ação prática"},
        ],
    }


def valid_micro_script():
    return {
        "contract_version": CONTRACT_VERSION,
        "language": "pt-BR",
        "full_narration": "O problema não é falta de tempo. Comece com um passo pequeno.",
        "blocks": [
            {"id": "m1", "text": "O problema não é falta de tempo.", "target_duration_seconds": 3.2, "narrative_function": "hook", "vocal_intent": "Contraste firme", "emphasis_terms": ["problema", "tempo"], "pause_after_seconds": 0.2},
            {"id": "m2", "text": "Comece com um passo pequeno.", "target_duration_seconds": 2.8, "narrative_function": "payoff", "vocal_intent": "Convite calmo", "emphasis_terms": ["passo pequeno"], "pause_after_seconds": 0},
        ],
    }


def valid_visual_direction():
    return {
        "contract_version": CONTRACT_VERSION,
        "visual_bible": {
            "palette": "Âmbar, azul profundo e pretos neutros",
            "lighting_language": "Contraluz suave com fontes laterais",
            "lens_language": "Planos médios e detalhes com profundidade rasa",
            "texture": "Grão cinematográfico discreto",
            "composition_rules": "Espaço negativo para texto na área segura",
            "continuity_rules": "Manter protagonista, figurino e temperatura de cor",
        },
        "beats": [
            {"block_id": "m1", "spoken_intent": "Quebrar uma crença", "emotion": "Surpresa contida", "metaphor": "Relógio parado diante de uma porta aberta", "visible_action": "Pessoa atravessa a porta enquanto o relógio permanece parado", "subject": "Pessoa adulta", "environment": "Corredor minimalista", "shot_design": "Plano médio lateral", "camera_move": "Push-in lento", "continuity_note": "Manter figurino escuro", "media_route": "ai_image_motion"},
            {"block_id": "m2", "spoken_intent": "Sugerir ação simples", "emotion": "Alívio", "metaphor": "Primeira luz entrando por uma fresta", "visible_action": "Mão abre lentamente a cortina", "subject": "Mão e cortina", "environment": "Quarto ao amanhecer", "shot_design": "Close-up", "camera_move": "Static", "continuity_note": "Manter paleta âmbar", "media_route": "stock_video"},
        ],
    }


def valid_edit_timeline():
    return {
        "contract_version": CONTRACT_VERSION,
        "audio_asset_id": "narration-final.wav",
        "alignment_method": "word-aligner-v1",
        "alignment_level": "word",
        "audio_duration_seconds": 6.0,
        "word_timestamps": [
            {"text": "O", "start_seconds": 0.0, "end_seconds": 0.1, "confidence": 0.99},
            {"text": "problema", "start_seconds": 0.11, "end_seconds": 0.8, "confidence": 0.95},
        ],
        "edit_anchors": [
            {"block_id": "m1", "trigger_text": "problema", "at_seconds": 0.11, "alignment_level": "word", "visual_event": "Corte para o plano de porta", "sfx": None},
        ],
        "caption_events": [],
        "audio_mix_events": [],
    }


class EditorialPipelineContractTests(unittest.TestCase):
    def test_valid_hook_strategy_passes(self):
        self.assertEqual(validate_hook_strategy(valid_hook_strategy()), [])

    def test_hook_strategy_requires_three_distinct_hook_angles(self):
        data = valid_hook_strategy()
        data["hook_candidates"][2]["type"] = "curiosity"
        errors = validate_hook_strategy(data)
        self.assertTrue(any("exactly 3" in error for error in errors) is False)
        self.assertTrue(any("must be distinct" in error for error in errors))

    def test_hook_strategy_requires_selected_candidate_reference(self):
        data = valid_hook_strategy()
        data["selected_hook_type"] = "unknown"
        self.assertTrue(any("selected_hook_type" in error for error in validate_hook_strategy(data)))

    def test_micro_script_reconstructs_full_narration(self):
        self.assertEqual(validate_micro_script(valid_micro_script()), [])

    def test_micro_script_rejects_text_drift(self):
        data = valid_micro_script()
        data["blocks"][1]["text"] = "Faça algo diferente."
        self.assertTrue(any("must match full_narration" in error for error in validate_micro_script(data)))

    def test_micro_script_uses_target_range_as_guideline_not_hard_limit(self):
        data = valid_micro_script()
        data["blocks"][0]["target_duration_seconds"] = 4.2
        self.assertEqual(validate_micro_script(data), [])

    def test_micro_script_rejects_duplicate_block_ids(self):
        data = valid_micro_script()
        data["blocks"][1]["id"] = "m1"
        self.assertTrue(any("duplicate block id" in error for error in validate_micro_script(data)))

    def test_visual_direction_requires_a_visual_bible(self):
        self.assertEqual(validate_visual_direction(valid_visual_direction()), [])
        data = valid_visual_direction()
        del data["visual_bible"]["palette"]
        self.assertTrue(any("palette" in error for error in validate_visual_direction(data)))

    def test_visual_direction_rejects_unrecognized_media_route(self):
        data = valid_visual_direction()
        data["beats"][0]["media_route"] = "whatever"
        self.assertTrue(any("media_route" in error for error in validate_visual_direction(data)))

    def test_visual_direction_rejects_duplicate_beat_ids(self):
        data = valid_visual_direction()
        data["beats"][1]["block_id"] = "m1"
        self.assertTrue(any("duplicate visual beat" in error for error in validate_visual_direction(data)))

    def test_edit_timeline_accepts_word_alignment(self):
        self.assertEqual(validate_edit_timeline(valid_edit_timeline()), [])

    def test_edit_timeline_rejects_unordered_word_timestamps(self):
        data = valid_edit_timeline()
        data["word_timestamps"][1]["start_seconds"] = 0.05
        self.assertTrue(any("not time ordered" in error for error in validate_edit_timeline(data)))

    def test_edit_timeline_rejects_timestamp_beyond_audio(self):
        data = valid_edit_timeline()
        data["word_timestamps"][1]["end_seconds"] = 6.5
        self.assertTrue(any("exceeds audio duration" in error for error in validate_edit_timeline(data)))

    def test_phoneme_anchor_requires_phoneme_level_alignment(self):
        data = valid_edit_timeline()
        data["edit_anchors"][0].update({"alignment_level": "phoneme", "phoneme": "ˈp"})
        self.assertTrue(any("anchor precision exceeds available alignment level" in error for error in validate_edit_timeline(data)))


    def test_character_alignment_requires_character_timestamps(self):
        data = valid_edit_timeline()
        data["alignment_level"] = "character"
        self.assertTrue(any("required for character-level alignment" in error for error in validate_edit_timeline(data)))

    def test_character_anchor_requires_a_matching_character_timestamp(self):
        data = valid_edit_timeline()
        data["alignment_level"] = "character"
        data["character_timestamps"] = [
            {"text": "p", "start_seconds": 0.2, "end_seconds": 0.3, "confidence": 0.9}
        ]
        data["edit_anchors"][0].update({
            "alignment_level": "character",
            "character": "p",
            "at_seconds": 0.25,
        })
        self.assertEqual(validate_edit_timeline(data), [])

    def test_phoneme_anchor_requires_phoneme_label(self):
        data = valid_edit_timeline()
        data["alignment_level"] = "phoneme"
        data["edit_anchors"][0]["alignment_level"] = "phoneme"
        self.assertTrue(any(".phoneme:" in error for error in validate_edit_timeline(data)))


    def test_pipeline_requires_visual_direction_for_every_micro_block(self):
        pipeline = {
            "hook_strategy": valid_hook_strategy(),
            "micro_script": valid_micro_script(),
            "visual_direction": valid_visual_direction(),
            "edit_timeline": valid_edit_timeline(),
        }
        pipeline["visual_direction"]["beats"].pop()
        from nexus.editorial_pipeline import validate_editorial_pipeline
        errors = validate_editorial_pipeline(pipeline)
        self.assertTrue(any("missing visual direction for micro block m2" in error for error in errors["visual_direction"]))

    def test_pipeline_rejects_edit_anchor_for_unknown_micro_block(self):
        pipeline = {
            "hook_strategy": valid_hook_strategy(),
            "micro_script": valid_micro_script(),
            "visual_direction": valid_visual_direction(),
            "edit_timeline": valid_edit_timeline(),
        }
        pipeline["edit_timeline"]["edit_anchors"][0]["block_id"] = "missing"
        from nexus.editorial_pipeline import validate_editorial_pipeline
        errors = validate_editorial_pipeline(pipeline)
        self.assertTrue(any("unknown micro block reference" in error for error in errors["edit_timeline"]))

    def test_selected_hook_must_open_the_micro_script(self):
        pipeline = {
            "hook_strategy": valid_hook_strategy(),
            "micro_script": valid_micro_script(),
            "visual_direction": valid_visual_direction(),
            "edit_timeline": valid_edit_timeline(),
        }
        pipeline["micro_script"]["blocks"][0]["text"] = "Uma ideia completamente diferente."
        pipeline["micro_script"]["full_narration"] = "Uma ideia completamente diferente. Comece com um passo pequeno."
        from nexus.editorial_pipeline import validate_editorial_pipeline
        errors = validate_editorial_pipeline(pipeline)
        self.assertTrue(any("selected hook must appear" in error for error in errors["micro_script"]))


    def test_micro_script_duration_guidance_is_advisory(self):
        data = valid_micro_script()
        data["blocks"][0]["target_duration_seconds"] = 4.2
        self.assertEqual(validate_micro_script(data), [])
        self.assertTrue(any("outside the preferred 2.5–3.5s range" in item for item in micro_script_advisories(data)))

    def test_edit_anchor_must_match_word_timestamp_and_location(self):
        data = valid_edit_timeline()
        data["edit_anchors"][0]["trigger_text"] = "tempo"
        self.assertTrue(any("no matching aligned word" in error for error in validate_edit_timeline(data)))
        data = valid_edit_timeline()
        data["edit_anchors"][0]["at_seconds"] = 2.0
        self.assertTrue(any("falls outside the aligned trigger word" in error for error in validate_edit_timeline(data)))

    def test_injected_four_brain_runner_executes_in_order_without_network(self):
        calls = []
        audio = {"audio_asset_id": "narration-final.wav", "duration_seconds": 6.0}

        def strategist(brief):
            calls.append(("brain1", brief["topic"]))
            return valid_hook_strategy()

        def scriptwriter(payload):
            calls.append(("brain2", payload["hook_strategy"]["selected_hook_type"]))
            return valid_micro_script()

        def photographer(payload):
            calls.append(("brain3", len(payload["micro_script"]["blocks"])))
            return valid_visual_direction()

        def editor(payload):
            calls.append(("brain4", payload["narration_audio"]["audio_asset_id"]))
            return valid_edit_timeline()

        result = run_four_brain_pipeline(
            {"topic": "teste"},
            strategist=strategist,
            scriptwriter=scriptwriter,
            photographer=photographer,
            editor=editor,
            narration_audio=audio,
        )
        self.assertEqual([item[0] for item in calls], ["brain1", "brain2", "brain3", "brain4"])
        self.assertEqual(result["narration_audio"], audio)
        self.assertEqual(result["edit_timeline"]["audio_asset_id"], audio["audio_asset_id"])

    def test_injected_runner_stops_when_a_brain_fails_validation(self):
        calls = []

        def strategist(brief):
            calls.append("brain1")
            result = valid_hook_strategy()
            result["hook_candidates"] = []
            return result

        with self.assertRaisesRegex(ValueError, "Brain 1 rejected"):
            run_four_brain_pipeline(
                {"topic": "teste"},
                strategist=strategist,
                scriptwriter=lambda payload: calls.append("brain2"),
                photographer=lambda payload: calls.append("brain3"),
                editor=lambda payload: calls.append("brain4"),
                narration_audio={"audio_asset_id": "audio.wav", "duration_seconds": 6.0},
            )
        self.assertEqual(calls, ["brain1"])

    def test_full_pipeline_reports_each_brain_independently(self):
        pipeline = {
            "hook_strategy": valid_hook_strategy(),
            "micro_script": valid_micro_script(),
            "visual_direction": valid_visual_direction(),
            "edit_timeline": valid_edit_timeline(),
        }
        self.assertTrue(editorial_pipeline_is_valid(pipeline))
        pipeline["visual_direction"]["beats"][0]["media_route"] = "unknown"
        self.assertFalse(editorial_pipeline_is_valid(pipeline))


if __name__ == "__main__":
    unittest.main()
