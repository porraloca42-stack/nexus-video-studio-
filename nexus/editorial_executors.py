"""Dependency-injected adapters from editorial prompt builders to model executors.

No credentials, network clients or model SDKs are imported here. A caller must
explicitly inject a callable; tests can use deterministic local executors.
"""
from collections.abc import Callable
from typing import Any

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
