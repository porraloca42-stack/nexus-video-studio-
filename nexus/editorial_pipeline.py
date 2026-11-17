"""Versioned, dependency-free contracts for the NEXUS four-brain editorial pipeline.

This module validates stage artifacts only. It does not call models, APIs, audio
services, renderers, or external aligners; it is safe for deterministic CI tests.
"""
from __future__ import annotations

from typing import Any


CONTRACT_VERSION = "1.0"

HOOK_TYPES = {"curiosity", "loss_opportunity", "pattern_break"}
MEDIA_ROUTES = {
    "stock_video",
    "ai_image_motion",
    "parallax_2_5d",
    "overlay",
    "motion_graphics",
    "ai_video",
    "user_media",
}
NARRATIVE_FUNCTIONS = {
    "hook", "setup", "development", "contrast", "reveal", "payoff", "cta", "loop_bridge"
}
ALIGNMENT_LEVELS = {"word", "character", "phoneme"}


def _is_object(value: Any) -> bool:
    return isinstance(value, dict)


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require_string(obj: dict, key: str, path: str, errors: list[str]) -> None:
    if not _is_nonempty_string(obj.get(key)):
        errors.append(f"{path}.{key}: expected non-empty string")


def _require_number(obj: dict, key: str, path: str, errors: list[str], *, minimum=None, maximum=None) -> None:
    value = obj.get(key)
    if not _is_number(value):
        errors.append(f"{path}.{key}: expected number")
        return
    if minimum is not None and value < minimum:
        errors.append(f"{path}.{key}: must be >= {minimum}")
    if maximum is not None and value > maximum:
        errors.append(f"{path}.{key}: must be <= {maximum}")


def _require_list(obj: dict, key: str, path: str, errors: list[str]) -> list:
    value = obj.get(key)
    if not isinstance(value, list):
        errors.append(f"{path}.{key}: expected array")
        return []
    return value


def validate_hook_strategy(data: Any) -> list[str]:
    """Validate Brain 1: three distinct hook angles and a coherent narrative arc."""
    errors: list[str] = []
    path = "hook_strategy"
    if not _is_object(data):
        return [f"{path}: expected object"]
    if data.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"{path}.contract_version: unsupported or missing version")

    candidates = _require_list(data, "hook_candidates", path, errors)
    if len(candidates) != 3:
        errors.append(f"{path}.hook_candidates: expected exactly 3 candidates")
    seen_types = set()
    for index, candidate in enumerate(candidates):
        item_path = f"{path}.hook_candidates[{index}]"
        if not _is_object(candidate):
            errors.append(f"{item_path}: expected object")
            continue
        hook_type = candidate.get("type")
        if hook_type not in HOOK_TYPES:
            errors.append(f"{item_path}.type: unsupported hook type")
        elif hook_type in seen_types:
            errors.append(f"{item_path}.type: hook angles must be distinct")
        else:
            seen_types.add(hook_type)
        _require_string(candidate, "text", item_path, errors)
        _require_string(candidate, "rationale", item_path, errors)

    selected_type = data.get("selected_hook_type")
    if selected_type not in HOOK_TYPES:
        errors.append(f"{path}.selected_hook_type: unsupported hook type")
    elif selected_type not in seen_types:
        errors.append(f"{path}.selected_hook_type: must reference one candidate")
    _require_string(data, "selected_hook", path, errors)
    _require_string(data, "selection_reason", path, errors)
    _require_string(data, "narrative_promise", path, errors)
    _require_string(data, "payoff", path, errors)
    _require_string(data, "ending_loop_bridge", path, errors)

    beats = _require_list(data, "narrative_beats", path, errors)
    if len(beats) < 2:
        errors.append(f"{path}.narrative_beats: expected at least 2 beats")
    for index, beat in enumerate(beats):
        item_path = f"{path}.narrative_beats[{index}]"
        if not _is_object(beat):
            errors.append(f"{item_path}: expected object")
            continue
        _require_string(beat, "id", item_path, errors)
        _require_string(beat, "purpose", item_path, errors)
        _require_number(beat, "tension_level", item_path, errors, minimum=0, maximum=5)
        _require_string(beat, "expected_payoff", item_path, errors)
    return errors


def validate_micro_script(data: Any) -> list[str]:
    """Validate Brain 2: short oral blocks that reconstruct the complete narration."""
    errors: list[str] = []
    path = "micro_script"
    if not _is_object(data):
        return [f"{path}: expected object"]
    if data.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"{path}.contract_version: unsupported or missing version")
    _require_string(data, "full_narration", path, errors)
    _require_string(data, "language", path, errors)
    blocks = _require_list(data, "blocks", path, errors)
    if not blocks:
        errors.append(f"{path}.blocks: expected at least 1 block")

    reconstructed = []
    seen_ids = set()
    for index, block in enumerate(blocks):
        item_path = f"{path}.blocks[{index}]"
        if not _is_object(block):
            errors.append(f"{item_path}: expected object")
            continue
        block_id = block.get("id")
        if not _is_nonempty_string(block_id):
            errors.append(f"{item_path}.id: expected non-empty string")
        elif block_id in seen_ids:
            errors.append(f"{item_path}.id: duplicate block id")
        else:
            seen_ids.add(block_id)
        _require_string(block, "text", item_path, errors)
        if _is_nonempty_string(block.get("text")):
            reconstructed.append(block["text"].strip())
        _require_number(block, "target_duration_seconds", item_path, errors, minimum=0.5, maximum=8.0)
        function = block.get("narrative_function")
        if function not in NARRATIVE_FUNCTIONS:
            errors.append(f"{item_path}.narrative_function: unsupported function")
        _require_string(block, "vocal_intent", item_path, errors)
        emphasis = block.get("emphasis_terms")
        if not isinstance(emphasis, list) or any(not _is_nonempty_string(term) for term in emphasis):
            errors.append(f"{item_path}.emphasis_terms: expected array of non-empty strings")
        _require_number(block, "pause_after_seconds", item_path, errors, minimum=0, maximum=3)

    full = data.get("full_narration")
    if _is_nonempty_string(full) and reconstructed:
        normalize = lambda value: " ".join(value.split())
        if normalize(" ".join(reconstructed)) != normalize(full):
            errors.append(f"{path}.blocks: concatenated text must match full_narration")
    return errors


def validate_visual_direction(data: Any) -> list[str]:
    """Validate Brain 3: visual bible and one semantically grounded direction per beat."""
    errors: list[str] = []
    path = "visual_direction"
    if not _is_object(data):
        return [f"{path}: expected object"]
    if data.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"{path}.contract_version: unsupported or missing version")
    bible = data.get("visual_bible")
    if not _is_object(bible):
        errors.append(f"{path}.visual_bible: expected object")
        bible = {}
    for field in ("palette", "lighting_language", "lens_language", "texture", "composition_rules", "continuity_rules"):
        _require_string(bible, field, f"{path}.visual_bible", errors)

    beats = _require_list(data, "beats", path, errors)
    if not beats:
        errors.append(f"{path}.beats: expected at least 1 beat")
    seen_blocks = set()
    for index, beat in enumerate(beats):
        item_path = f"{path}.beats[{index}]"
        if not _is_object(beat):
            errors.append(f"{item_path}: expected object")
            continue
        _require_string(beat, "block_id", item_path, errors)
        block_id = beat.get("block_id")
        if block_id in seen_blocks:
            errors.append(f"{item_path}.block_id: duplicate visual beat")
        seen_blocks.add(block_id)
        for field in ("spoken_intent", "emotion", "metaphor", "visible_action", "subject", "environment", "shot_design", "camera_move", "continuity_note"):
            _require_string(beat, field, item_path, errors)
        if beat.get("media_route") not in MEDIA_ROUTES:
            errors.append(f"{item_path}.media_route: unsupported media route")
    return errors


def validate_edit_timeline(data: Any) -> list[str]:
    """Validate Brain 4: measured audio alignment and time-ordered edit events."""
    errors: list[str] = []
    path = "edit_timeline"
    if not _is_object(data):
        return [f"{path}: expected object"]
    if data.get("contract_version") != CONTRACT_VERSION:
        errors.append(f"{path}.contract_version: unsupported or missing version")
    _require_string(data, "audio_asset_id", path, errors)
    _require_string(data, "alignment_method", path, errors)
    _require_number(data, "audio_duration_seconds", path, errors, minimum=0.01)
    alignment_level = data.get("alignment_level")
    if alignment_level not in ALIGNMENT_LEVELS:
        errors.append(f"{path}.alignment_level: expected word, character or phoneme")

    words = _require_list(data, "word_timestamps", path, errors)
    character_times = data.get("character_timestamps", [])
    phoneme_times = data.get("phoneme_timestamps", [])
    if not isinstance(character_times, list):
        errors.append(f"{path}.character_timestamps: expected array")
        character_times = []
    if not isinstance(phoneme_times, list):
        errors.append(f"{path}.phoneme_timestamps: expected array")
        phoneme_times = []
    if alignment_level == "character" and not character_times:
        errors.append(f"{path}.character_timestamps: required for character-level alignment")
    if alignment_level == "phoneme" and not phoneme_times:
        errors.append(f"{path}.phoneme_timestamps: required for phoneme-level alignment")
    previous_end = 0.0
    for index, word in enumerate(words):
        item_path = f"{path}.word_timestamps[{index}]"
        if not _is_object(word):
            errors.append(f"{item_path}: expected object")
            continue
        _require_string(word, "text", item_path, errors)
        start = word.get("start_seconds")
        end = word.get("end_seconds")
        if not _is_number(start) or not _is_number(end):
            errors.append(f"{item_path}: start_seconds and end_seconds must be numbers")
            continue
        if start < 0 or end <= start:
            errors.append(f"{item_path}: invalid timestamp interval")
        if start < previous_end - 0.02:
            errors.append(f"{item_path}: timestamps are not time ordered")
        previous_end = end
        if _is_number(data.get("audio_duration_seconds")) and end > data["audio_duration_seconds"] + 0.05:
            errors.append(f"{item_path}: timestamp exceeds audio duration")
        if not _is_number(word.get("confidence")) or not 0 <= word["confidence"] <= 1:
            errors.append(f"{item_path}.confidence: expected value between 0 and 1")

    def validate_fine_timestamps(items, field_name):
        previous = 0.0
        for index, item in enumerate(items):
            item_path = f"{path}.{field_name}[{index}]"
            if not _is_object(item):
                errors.append(f"{item_path}: expected object")
                continue
            _require_string(item, "text", item_path, errors)
            start, end = item.get("start_seconds"), item.get("end_seconds")
            if not _is_number(start) or not _is_number(end):
                errors.append(f"{item_path}: start_seconds and end_seconds must be numbers")
                continue
            if start < 0 or end <= start or start < previous - 0.02:
                errors.append(f"{item_path}: invalid or unordered timestamp interval")
            if _is_number(data.get("audio_duration_seconds")) and end > data["audio_duration_seconds"] + 0.05:
                errors.append(f"{item_path}: timestamp exceeds audio duration")
            previous = end

    validate_fine_timestamps(character_times, "character_timestamps")
    validate_fine_timestamps(phoneme_times, "phoneme_timestamps")

    anchors = _require_list(data, "edit_anchors", path, errors)
    aligned_words = [
        word for word in words
        if _is_object(word) and _is_nonempty_string(word.get("text"))
        and _is_number(word.get("start_seconds")) and _is_number(word.get("end_seconds"))
    ]
    last_anchor = -1.0
    for index, anchor in enumerate(anchors):
        item_path = f"{path}.edit_anchors[{index}]"
        if not _is_object(anchor):
            errors.append(f"{item_path}: expected object")
            continue
        _require_string(anchor, "block_id", item_path, errors)
        _require_string(anchor, "trigger_text", item_path, errors)
        _require_number(anchor, "at_seconds", item_path, errors, minimum=0)
        if _is_number(anchor.get("at_seconds")):
            if anchor["at_seconds"] < last_anchor:
                errors.append(f"{item_path}.at_seconds: anchors must be time ordered")
            last_anchor = anchor["at_seconds"]
            if _is_number(data.get("audio_duration_seconds")) and anchor["at_seconds"] > data["audio_duration_seconds"]:
                errors.append(f"{item_path}.at_seconds: anchor exceeds audio duration")
        anchor_level = anchor.get("alignment_level")
        if anchor_level not in ALIGNMENT_LEVELS:
            errors.append(f"{item_path}.alignment_level: expected word or phoneme")
        alignment_rank = {"word": 1, "character": 2, "phoneme": 3}
        if anchor_level in ALIGNMENT_LEVELS and alignment_level in ALIGNMENT_LEVELS:
            if alignment_rank[anchor_level] > alignment_rank[alignment_level]:
                errors.append(f"{item_path}: anchor precision exceeds available alignment level")
        if anchor_level == "phoneme":
            _require_string(anchor, "phoneme", item_path, errors)
            if not phoneme_times:
                errors.append(f"{item_path}: phoneme anchor requires phoneme_timestamps")
            elif _is_nonempty_string(anchor.get("phoneme")):
                matches = [item for item in phoneme_times if _is_object(item) and item.get("text") == anchor["phoneme"]]
                if not matches:
                    errors.append(f"{item_path}.phoneme: no matching aligned phoneme")
                elif _is_number(anchor.get("at_seconds")) and not any(
                    item["start_seconds"] - 0.05 <= anchor["at_seconds"] <= item["end_seconds"] + 0.05
                    for item in matches
                ):
                    errors.append(f"{item_path}.at_seconds: anchor falls outside the aligned phoneme")
        if anchor_level == "character":
            _require_string(anchor, "character", item_path, errors)
            if not character_times:
                errors.append(f"{item_path}: character anchor requires character_timestamps")
            elif _is_nonempty_string(anchor.get("character")):
                matches = [item for item in character_times if _is_object(item) and item.get("text") == anchor["character"]]
                if not matches:
                    errors.append(f"{item_path}.character: no matching aligned character")
                elif _is_number(anchor.get("at_seconds")) and not any(
                    item["start_seconds"] - 0.05 <= anchor["at_seconds"] <= item["end_seconds"] + 0.05
                    for item in matches
                ):
                    errors.append(f"{item_path}.at_seconds: anchor falls outside the aligned character")
        if anchor_level == "word" and _is_nonempty_string(anchor.get("trigger_text")):
            matching = [
                word for word in aligned_words
                if word["text"].strip().casefold() == anchor["trigger_text"].strip().casefold()
            ]
            if not matching:
                errors.append(f"{item_path}.trigger_text: no matching aligned word")
            elif _is_number(anchor.get("at_seconds")) and not any(
                word["start_seconds"] - 0.05 <= anchor["at_seconds"] <= word["end_seconds"] + 0.05
                for word in matching
            ):
                errors.append(f"{item_path}.at_seconds: anchor falls outside the aligned trigger word")
        _require_string(anchor, "visual_event", item_path, errors)
        sfx = anchor.get("sfx")
        if sfx is not None and not _is_nonempty_string(sfx):
            errors.append(f"{item_path}.sfx: expected non-empty string or null")

    caption_events = _require_list(data, "caption_events", path, errors)
    for index, event in enumerate(caption_events):
        item_path = f"{path}.caption_events[{index}]"
        if not _is_object(event):
            errors.append(f"{item_path}: expected object")
            continue
        _require_string(event, "id", item_path, errors)
        _require_string(event, "text", item_path, errors)
        _require_number(event, "start_seconds", item_path, errors, minimum=0)
        _require_number(event, "end_seconds", item_path, errors, minimum=0)
        if _is_number(event.get("start_seconds")) and _is_number(event.get("end_seconds")):
            if event["end_seconds"] <= event["start_seconds"]:
                errors.append(f"{item_path}: end_seconds must be after start_seconds")
            if _is_number(data.get("audio_duration_seconds")) and event["end_seconds"] > data["audio_duration_seconds"] + 0.05:
                errors.append(f"{item_path}: caption exceeds audio duration")
        if event.get("position", "bottom") not in {"top", "center", "bottom"}:
            errors.append(f"{item_path}.position: expected top, center or bottom")
        words = event.get("words", [])
        if not isinstance(words, list):
            errors.append(f"{item_path}.words: expected array")
            continue
        previous_word_end = event.get("start_seconds", 0)
        for word_index, word in enumerate(words):
            word_path = f"{item_path}.words[{word_index}]"
            if not _is_object(word):
                errors.append(f"{word_path}: expected object")
                continue
            _require_string(word, "text", word_path, errors)
            start, end = word.get("start_seconds"), word.get("end_seconds")
            if not _is_number(start) or not _is_number(end):
                errors.append(f"{word_path}: start_seconds and end_seconds must be numbers")
                continue
            if start < previous_word_end - 0.02 or end <= start:
                errors.append(f"{word_path}: invalid or unordered word interval")
            if _is_number(event.get("start_seconds")) and start < event["start_seconds"] - 0.05:
                errors.append(f"{word_path}: word starts before caption cue")
            if _is_number(event.get("end_seconds")) and end > event["end_seconds"] + 0.05:
                errors.append(f"{word_path}: word ends after caption cue")
            previous_word_end = end

    sfx_events = _require_list(data, "sfx_events", path, errors)
    for index, event in enumerate(sfx_events):
        item_path = f"{path}.sfx_events[{index}]"
        if not _is_object(event):
            errors.append(f"{item_path}: expected object")
            continue
        for field in ("id", "asset_path"):
            _require_string(event, field, item_path, errors)
        _require_number(event, "start_seconds", item_path, errors, minimum=0)
        _require_number(event, "duration_seconds", item_path, errors, minimum=0.01)
        _require_number(event, "volume", item_path, errors, minimum=0, maximum=1)
        if _is_number(event.get("start_seconds")) and _is_number(event.get("duration_seconds")) and _is_number(data.get("audio_duration_seconds")):
            if event["start_seconds"] + event["duration_seconds"] > data["audio_duration_seconds"] + 0.05:
                errors.append(f"{item_path}: sound effect exceeds audio duration")

    mix_events = _require_list(data, "audio_mix_events", path, errors)
    for index, event in enumerate(mix_events):
        item_path = f"{path}.audio_mix_events[{index}]"
        if not _is_object(event):
            errors.append(f"{item_path}: expected object")
            continue
        _require_number(event, "start_seconds", item_path, errors, minimum=0)
        _require_number(event, "end_seconds", item_path, errors, minimum=0)
        _require_number(event, "music_volume", item_path, errors, minimum=0, maximum=1)
        if _is_number(event.get("start_seconds")) and _is_number(event.get("end_seconds")):
            if event["end_seconds"] <= event["start_seconds"]:
                errors.append(f"{item_path}: end_seconds must be after start_seconds")
            if _is_number(data.get("audio_duration_seconds")) and event["end_seconds"] > data["audio_duration_seconds"] + 0.05:
                errors.append(f"{item_path}: mix event exceeds audio duration")
    return errors


def validate_editorial_pipeline(data: Any) -> dict[str, list[str]]:
    """Return per-brain validation errors without making external calls."""
    if not _is_object(data):
        message = ["pipeline: expected object"]
        return {name: message for name in ("hook_strategy", "micro_script", "visual_direction", "edit_timeline")}
    hook_errors = validate_hook_strategy(data.get("hook_strategy"))
    script_errors = validate_micro_script(data.get("micro_script"))
    visual_errors = validate_visual_direction(data.get("visual_direction"))
    edit_errors = validate_edit_timeline(data.get("edit_timeline"))

    script = data.get("micro_script")
    visual = data.get("visual_direction")
    edit = data.get("edit_timeline")
    if _is_object(script) and _is_object(visual):
        script_ids = {
            block.get("id") for block in script.get("blocks", [])
            if _is_object(block) and _is_nonempty_string(block.get("id"))
        }
        visual_ids = {
            beat.get("block_id") for beat in visual.get("beats", [])
            if _is_object(beat) and _is_nonempty_string(beat.get("block_id"))
        }
        for missing in sorted(script_ids - visual_ids):
            visual_errors.append(f"visual_direction.beats: missing visual direction for micro block {missing}")
        for extra in sorted(visual_ids - script_ids):
            visual_errors.append(f"visual_direction.beats: unknown micro block reference {extra}")
    if _is_object(script) and _is_object(edit):
        script_ids = {
            block.get("id") for block in script.get("blocks", [])
            if _is_object(block) and _is_nonempty_string(block.get("id"))
        }
        for index, anchor in enumerate(edit.get("edit_anchors", [])):
            if _is_object(anchor) and anchor.get("block_id") not in script_ids:
                edit_errors.append(f"edit_timeline.edit_anchors[{index}].block_id: unknown micro block reference")

    if _is_object(hook := data.get("hook_strategy")) and _is_object(script):
        candidates = hook.get("hook_candidates", [])
        selected = next(
            (item.get("text") for item in candidates
             if _is_object(item) and item.get("type") == hook.get("selected_hook_type")),
            None,
        ) if isinstance(candidates, list) else None
        blocks = script.get("blocks", [])
        if _is_nonempty_string(selected) and isinstance(blocks, list) and blocks and _is_object(blocks[0]):
            first_text = str(blocks[0].get("text") or "").strip()
            if selected.casefold() not in first_text.casefold():
                script_errors.append("micro_script.blocks[0].text: selected hook must appear in the opening block")

    return {
        "hook_strategy": hook_errors,
        "micro_script": script_errors,
        "visual_direction": visual_errors,
        "edit_timeline": edit_errors,
    }


def micro_script_advisories(data: Any) -> list[str]:
    """Non-blocking guidance for the preferred 2.5–3.5s micro-rhythm."""
    if not _is_object(data) or not isinstance(data.get("blocks"), list):
        return []
    advisories = []
    for index, block in enumerate(data["blocks"], 1):
        if not _is_object(block) or not _is_number(block.get("target_duration_seconds")):
            continue
        duration = block["target_duration_seconds"]
        if not 2.5 <= duration <= 3.5:
            advisories.append(
                f"micro_script.blocks[{index - 1}]: {duration:.2f}s is outside the preferred 2.5–3.5s range; "
                "review editorially, but do not shorten a complete idea just to satisfy the heuristic."
            )
    return advisories


def run_four_brain_pipeline(
    brief: dict,
    *,
    strategist,
    scriptwriter,
    photographer,
    editor,
    narration_audio: dict,
) -> dict:
    """Run injected stage functions in order; safe for mocks and offline tests.

    Production integrations must explicitly provide the four stage executors and
    a final narration asset. This runner never discovers credentials or calls APIs.
    """
    if not _is_object(brief):
        raise ValueError("brief: expected object")
    if not _is_object(narration_audio):
        raise ValueError("narration_audio: expected object")
    if not _is_nonempty_string(narration_audio.get("audio_asset_id")):
        raise ValueError("narration_audio.audio_asset_id: expected non-empty string")
    if not _is_number(narration_audio.get("duration_seconds")) or narration_audio["duration_seconds"] <= 0:
        raise ValueError("narration_audio.duration_seconds: expected positive number")

    hook = strategist(brief)
    errors = validate_hook_strategy(hook)
    if errors:
        raise ValueError("Brain 1 rejected: " + "; ".join(errors))

    script = scriptwriter({"brief": brief, "hook_strategy": hook})
    errors = validate_micro_script(script)
    if errors:
        raise ValueError("Brain 2 rejected: " + "; ".join(errors))
    selected_hook = hook.get("selected_hook", "").casefold()
    if selected_hook not in script["blocks"][0]["text"].casefold():
        raise ValueError("Brain 2 rejected: selected hook is missing from opening block")

    visual = photographer({
        "brief": brief,
        "hook_strategy": hook,
        "micro_script": script,
    })
    errors = validate_visual_direction(visual)
    if errors:
        raise ValueError("Brain 3 rejected: " + "; ".join(errors))
    visual_ids = {beat["block_id"] for beat in visual["beats"]}
    script_ids = {block["id"] for block in script["blocks"]}
    if visual_ids != script_ids:
        raise ValueError("Brain 3 rejected: visual beats must map one-to-one to micro-script blocks")

    edit = editor({
        "brief": brief,
        "hook_strategy": hook,
        "micro_script": script,
        "visual_direction": visual,
        "narration_audio": narration_audio,
    })
    errors = validate_edit_timeline(edit)
    if errors:
        raise ValueError("Brain 4 rejected: " + "; ".join(errors))
    if edit.get("audio_asset_id") != narration_audio["audio_asset_id"]:
        raise ValueError("Brain 4 rejected: timeline audio_asset_id does not match final narration asset")
    if abs(edit.get("audio_duration_seconds", 0) - narration_audio["duration_seconds"]) > 0.05:
        raise ValueError("Brain 4 rejected: timeline duration does not match measured narration duration")

    return {
        "contract_version": CONTRACT_VERSION,
        "hook_strategy": hook,
        "micro_script": script,
        "visual_direction": visual,
        "narration_audio": narration_audio,
        "edit_timeline": edit,
        "micro_script_advisories": micro_script_advisories(script),
    }


def editorial_pipeline_is_valid(data: Any) -> bool:
    """Convenience predicate for gates; no implicit repair or fallback."""
    return all(not errors for errors in validate_editorial_pipeline(data).values())
