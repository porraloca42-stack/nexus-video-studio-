"""User-facing visual production modes and conservative defaults."""

ECONOMY_MODE = "Bibliotecas de vídeo · econômico (sem Modal)"
AI_VIDEO_MODE = "IA original · Cloudflare + Modal (usa créditos)"
RENDER_MODE_OPTIONS = (ECONOMY_MODE, AI_VIDEO_MODE)


def default_render_mode() -> str:
    """Avoid GPU and image-generation usage unless the user explicitly opts in."""
    return ECONOMY_MODE


def mode_uses_modal(mode: str) -> bool:
    """Return whether the selected visual mode dispatches work to Modal."""
    return mode == AI_VIDEO_MODE
