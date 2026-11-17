"""Fail-closed validation of the GPU requested by the Modal worker."""
from __future__ import annotations


_GPU_NAME_MARKERS = {
    "L40S": ("L40S",),
    "H100": ("H100",),
    "A10": ("A10",),
}


def validate_gpu_identity(requested_gpu_type: str, actual_gpu_name: str) -> dict:
    """Validate the CUDA device against the Modal GPU type before model loading.

    Raises when the runtime GPU cannot be identified or does not match the
    versioned request. This is an identity guard, not a billing measurement.
    """
    requested = str(requested_gpu_type or "").strip().upper()
    actual = str(actual_gpu_name or "").strip()
    if not actual or actual.lower() == "unknown":
        raise RuntimeError(
            f"GPU real não identificada; implantação solicitou {requested or 'desconhecida'}. "
            "Modelo não será carregado."
        )
    markers = _GPU_NAME_MARKERS.get(requested)
    if not markers:
        raise RuntimeError(
            f"Tipo de GPU solicitado sem regra de validação: {requested or 'vazio'}. "
            "Modelo não será carregado."
        )
    normalized = actual.upper()
    if not any(marker in normalized for marker in markers):
        raise RuntimeError(
            f"GPU incompatível: Modal solicitou {requested}, mas CUDA reportou {actual}. "
            "Modelo não será carregado."
        )
    return {
        "requested_gpu_type": requested,
        "actual_gpu_name": actual,
        "gpu_identity_verified": True,
    }
