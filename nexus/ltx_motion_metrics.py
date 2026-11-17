"""Lightweight temporal diagnostics for generated LTX frames.

These metrics flag near-static outputs for review; they are not proof of semantic motion.
"""
from __future__ import annotations

import numpy as np


def measure_temporal_motion(
    frames,
    *,
    pixel_delta_threshold: float = 6.0,
    active_pair_fraction_threshold: float = 0.005,
) -> dict:
    """Measure adjacent-frame pixel change without comparing only first/last frames."""
    array = np.asarray(frames)
    if array.ndim != 4 or array.shape[0] < 2:
        raise ValueError("frames must have shape (T, H, W, C) with at least two frames")
    if array.shape[-1] not in (1, 3, 4):
        raise ValueError("frames must contain 1, 3, or 4 channels")

    gray = array[..., :3].astype(np.float32).mean(axis=-1)
    differences = np.abs(np.diff(gray, axis=0))
    per_pair_mean = differences.mean(axis=(1, 2))
    per_pair_moving_fraction = (differences >= pixel_delta_threshold).mean(axis=(1, 2))
    active_pairs = per_pair_moving_fraction >= active_pair_fraction_threshold

    mean_moving_fraction = float(per_pair_moving_fraction.mean())
    active_pair_fraction = float(active_pairs.mean())
    return {
        "frame_count": int(array.shape[0]),
        "mean_abs_frame_difference": round(float(per_pair_mean.mean()), 4),
        "median_abs_frame_difference": round(float(np.median(per_pair_mean)), 4),
        "mean_moving_pixel_fraction": round(mean_moving_fraction, 6),
        "active_pair_fraction": round(active_pair_fraction, 6),
        "pixel_delta_threshold": float(pixel_delta_threshold),
        "active_pair_fraction_threshold": float(active_pair_fraction_threshold),
        "near_static_signal": bool(active_pair_fraction < 0.10 or mean_moving_fraction < 0.005),
        "interpretation": "diagnostic_only_requires_visual_review",
    }
