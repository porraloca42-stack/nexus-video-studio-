"""Explicit, bounded live smoke test for the optional Brain 4 Gemini executor.

The fixture is synthetic and never enters the production render path. Importing
this module performs no network calls; a single generation happens only when the
caller invokes run_brain4_live_smoke_test().
"""
from __future__ import annotations

from typing import Any, Callable

from nexus.editorial_executors import run_brain4_for_storyboard


FIXTURE_AUDIO = {
    "audio_asset_id": "nexus-brain4-smoke-fixture",
    "duration_seconds": 4.0,
    "provider": "synthetic_test_fixture",
    "alignment_method": "synthetic_word_timestamps_for_contract_smoke_test",
    "alignment_level": "word",
}

FIXTURE_WORD_TIMESTAMPS = [
    {"text": "Cada", "start_seconds": 0.10, "end_seconds": 0.42},
    {"text": "escolha", "start_seconds": 0.45, "end_seconds": 0.86},
    {"text": "visual", "start_seconds": 0.90, "end_seconds": 1.30},
    {"text": "precisa", "start_seconds": 1.45, "end_seconds": 1.84},
    {"text": "contar", "start_seconds": 1.90, "end_seconds": 2.25},
    {"text": "a", "start_seconds": 2.30, "end_seconds": 2.44},
    {"text": "mesma", "start_seconds": 2.50, "end_seconds": 2.84},
    {"text": "história.", "start_seconds": 2.90, "end_seconds": 3.60},
]

FIXTURE_PLAN = {
    "scenes": [
        {
            "voiceover": "Cada escolha visual",
            "duration_seconds": 1.3,
            "image_prompt": "A film director compares two contrasting visual compositions.",
            "camera_motion": "Slow controlled push-in",
            "subject": "film director",
            "environment": "editing studio",
            "shot_design": "medium close-up",
        },
        {
            "voiceover": "precisa contar a mesma história.",
            "duration_seconds": 2.7,
            "image_prompt": "A coherent sequence of film frames forms one visual narrative.",
            "camera_motion": "Gentle lateral tracking",
            "subject": "film frames",
            "environment": "cinematic editing suite",
            "shot_design": "wide over-the-shoulder",
        },
    ],
    "visual_continuity": "Neutral cinematic palette, controlled contrast",
}


def run_brain4_live_smoke_test(
    api_key: str,
    requested_model: str = "auto",
    *,
    model_call: Callable[[str], Any] | None = None,
) -> dict:
    """Execute one Brain 4 generation against synthetic evidence, then validate it.

    Supplying model_call is intended for offline tests only. The live path uses
    generate_editorial_json(), which is bounded to one model and one generation.
    """
    if not api_key and model_call is None:
        raise RuntimeError("GEMINI_API_KEY não está configurada.")

    if model_call is None:
        from nexus.director import generate_editorial_json

        model_call = lambda prompt: generate_editorial_json(
            prompt, api_key, requested_model=requested_model
        )

    result = run_brain4_for_storyboard(
        FIXTURE_PLAN,
        narration_audio=FIXTURE_AUDIO,
        word_timestamps=FIXTURE_WORD_TIMESTAMPS,
        model_call=model_call,
    )
    timeline = result["edit_timeline"]
    return {
        "status": "brain4_validated",
        "audio_duration_seconds": FIXTURE_AUDIO["duration_seconds"],
        "alignment_level": timeline["alignment_level"],
        "caption_event_count": len(timeline.get("caption_events", [])),
        "edit_anchor_count": len(timeline.get("edit_anchors", [])),
        "sfx_event_count": len(timeline.get("sfx_events", [])),
        "audio_mix_event_count": len(timeline.get("audio_mix_events", [])),
        "timeline": timeline,
    }
