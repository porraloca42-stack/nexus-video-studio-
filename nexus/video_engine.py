"""Stable scene-animation contract shared by NEXUS video engines.

The orchestration layer consumes native MP4 clips and telemetry only. Engine-
specific APIs, workers and workflow graphs stay behind this adapter boundary.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class VideoEngineError(RuntimeError):
    """Raised when a requested video engine is unavailable or misconfigured."""


class VideoEngine(Protocol):
    """Contract consumed by the NEXUS render orchestrator."""

    name: str

    def animate_scene_images(
        self,
        generated_images: list[dict[str, Any]],
        scenes: list[dict[str, Any]],
        output_dir: str | Path,
        *,
        progress_callback=None,
    ) -> list[dict[str, Any]]:
        """Return one validated MP4 path and telemetry record per scene."""


class LTX098VideoEngine:
    """Compatibility adapter for the currently deployed Modal LTX-0.9.8 worker."""

    name = "ltx098"

    def animate_scene_images(
        self,
        generated_images: list[dict[str, Any]],
        scenes: list[dict[str, Any]],
        output_dir: str | Path,
        *,
        progress_callback=None,
    ) -> list[dict[str, Any]]:
        from nexus.modal_i2v import animate_scene_images

        return animate_scene_images(
            generated_images,
            scenes,
            output_dir,
            progress_callback=progress_callback,
        )


def get_video_engine(name: str = "ltx098") -> VideoEngine:
    """Resolve an engine by stable name; never silently fall back on failure."""
    normalized = str(name or "").strip().lower()
    if normalized == "ltx098":
        return LTX098VideoEngine()
    if normalized == "ltx25_comfyui":
        raise VideoEngineError(
            "O motor LTX-2.5/ComfyUI ainda não está pronto para produção: "
            "o workflow API versionado e o adaptador de execução precisam ser "
            "integrados e testados antes de habilitar esta opção."
        )
    raise VideoEngineError(f"Motor de vídeo desconhecido: {normalized or '(vazio)'}.")
