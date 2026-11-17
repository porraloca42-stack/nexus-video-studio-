"""Dependency-injected adapters from editorial prompt builders to model executors.

No credentials, network clients or model SDKs are imported here. A caller must
explicitly inject a callable; tests can use deterministic local executors.
"""
from collections.abc import Callable
from typing import Any

from nexus.editorial_pipeline import validate_edit_timeline
from nexus.editorial_prompts import (
    build_edit_timeline_prompt,
    build_hook_strategy_prompt,
    build_micro_script_prompt,
    build_visual_direction_prompt,
)


def build_four_brain_executors(model_call: Callable[[str], Any]) -> dict[str, Callable]:
    """Bind the four pure prompt builders to one explicitly injected model call."""
    if not callable(model_call):
        raise TypeError("model_call must be an explicitly injected callable")

    def strategist(brief):
        return model_call(build_hook_strategy_prompt(brief))

    def scriptwriter(payload):
        return model_call(build_micro_script_prompt(
            payload["brief"], payload["hook_strategy"]
        ))

    def photographer(payload):
        return model_call(build_visual_direction_prompt(
            payload["brief"], payload["hook_strategy"], payload["micro_script"]
        ))

    def editor(payload):
        return model_call(build_edit_timeline_prompt(
            payload["micro_script"],
            payload["visual_direction"],
            payload["narration_audio"],
            payload.get("word_timestamps", []),
        ))

    return {
        "strategist": strategist,
        "scriptwriter": scriptwriter,
        "photographer": photographer,
        "editor": editor,
    }



def run_brain4_for_storyboard(
    plan: dict,
    *,
    narration_audio: dict,
    word_timestamps: list[dict],
    model_call: Callable[[str], Any],
) -> dict:
    """Run only Brain 4 against the existing approved storyboard and final audio.

    This adapter is opt-in through an explicitly injected model callable. It
    refuses to claim word synchronization when verified word timings are absent.
    """
    if not isinstance(plan, dict) or not isinstance(plan.get("scenes"), list):
        raise ValueError("plan.scenes must be an array")
    if not isinstance(narration_audio, dict):
        raise ValueError("narration_audio must be an object")
    if not isinstance(narration_audio.get("audio_asset_id"), str) or not narration_audio["audio_asset_id"]:
        raise ValueError("narration_audio.audio_asset_id is required")
    if not isinstance(narration_audio.get("duration_seconds"), (int, float)) or narration_audio["duration_seconds"] <= 0:
        raise ValueError("narration_audio.duration_seconds must be positive")
    if not word_timestamps:
        raise ValueError("Brain 4 requires verified word timestamps; no approximate timing is allowed")

    blocks = []
    visual_beats = []
    for index, scene in enumerate(plan["scenes"], 1):
        if not isinstance(scene, dict):
            raise ValueError(f"plan.scenes[{index - 1}] must be an object")
        text = str(scene.get("voiceover") or "").strip()
        if not text:
            raise ValueError(f"plan.scenes[{index - 1}].voiceover is required")
        block_id = f"scene-{index:02d}"
        blocks.append({
            "id": block_id,
            "text": text,
            "target_duration_seconds": float(
                scene.get("duration_seconds") or scene.get("duration") or 0
            ),
            "narrative_function": "development",
            "vocal_intent": "Preserve the already approved narration.",
            "emphasis_terms": [],
            "pause_after_seconds": 0.0,
        })
        visual_beats.append({
            "block_id": block_id,
            "spoken_intent": text,
            "emotion": str(scene.get("emotion") or "as specified by existing storyboard"),
            "metaphor": str(scene.get("image_prompt") or ""),
            "visible_action": str(scene.get("visible_action") or scene.get("image_prompt") or ""),
            "subject": str(scene.get("subject") or ""),
            "environment": str(scene.get("environment") or ""),
            "shot_design": str(scene.get("shot_design") or ""),
            "camera_move": str(scene.get("camera_motion") or "static"),
            "continuity_note": str(scene.get("continuity_note") or ""),
            "media_route": "ai_image_motion",
        })

    micro_script = {
        "contract_version": "1.0",
        "language": "pt-BR",
        "full_narration": " ".join(block["text"] for block in blocks),
        "blocks": blocks,
    }
    visual_direction = {
        "contract_version": "1.0",
        "visual_bible": {
            "palette": str(plan.get("visual_continuity") or "Preserve the existing storyboard palette"),
            "lighting_language": "Preserve approved scene lighting",
            "lens_language": "Preserve approved scene framing",
            "texture": "Preserve existing visual texture",
            "composition_rules": "Do not replace existing visual assets",
            "continuity_rules": "Respect the existing scene order and continuity",
        },
        "beats": visual_beats,
    }
    editor = build_four_brain_executors(model_call)["editor"]
    timeline = editor({
        "micro_script": micro_script,
        "visual_direction": visual_direction,
        "narration_audio": narration_audio,
        "word_timestamps": word_timestamps,
    })
    errors = validate_edit_timeline(timeline)
    if errors:
        raise ValueError("Brain 4 rejected: " + "; ".join(errors))
    if timeline.get("audio_asset_id") != narration_audio["audio_asset_id"]:
        raise ValueError("Brain 4 rejected: audio asset does not match the final narration")
    if abs(timeline.get("audio_duration_seconds", 0) - narration_audio["duration_seconds"]) > 0.05:
        raise ValueError("Brain 4 rejected: timeline duration does not match measured narration")
    updated_plan = dict(plan)
    updated_plan["edit_timeline"] = timeline
    updated_plan["editorial_pipeline"] = {
        "status": "brain4_validated",
        "executor": "explicitly_injected",
        "alignment_level": timeline["alignment_level"],
    }
    return updated_plan
