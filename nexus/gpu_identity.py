"""Fail-closed validation of the GPU requested by the Modal worker."""
from __future__ import annotations

import re


_GPU_NAME_PATTERNS = {
    "L40S": (r"(?<![A-Z0-9])L40S(?![A-Z0-9])",),
    "H100": (r"(?<![A-Z0-9])H100(?![A-Z0-9])",),
    # A10G is a valid A10 variant; token boundaries prevent matching A100.
    "A10": (r"(?<![A-Z0-9])A10G?(?![A-Z0-9])",),
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
    patterns = _GPU_NAME_PATTERNS.get(requested)
    if not markers:
        raise RuntimeError(
            f"Tipo de GPU solicitado sem regra de validação: {requested or 'vazio'}. "
            "Modelo não será carregado."
        )
    normalized = actual.upper()
    if not any(re.search(pattern, normalized) for pattern in patterns):
        raise RuntimeError(
            f"GPU incompatível: Modal solicitou {requested}, mas CUDA reportou {actual}. "
            "Modelo não será carregado."
        )
    return {
        "requested_gpu_type": requested,
        "actual_gpu_name": actual,
        "gpu_identity_verified": True,
    }
