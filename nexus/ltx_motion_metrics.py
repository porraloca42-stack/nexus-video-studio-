"""Lightweight temporal diagnostics for generated LTX frames.

Uses only the Python standard library so CI and the Modal worker share one implementation.
These metrics flag near-static outputs for review; they are not proof of semantic motion.
"""
from __future__ import annotations

import statistics


def measure_temporal_motion(
    frames,
    *,
    pixel_delta_threshold: float = 6.0,
    active_pair_fraction_threshold: float = 0.005,
) -> dict:
    """Measure adjacent-frame pixel change without comparing only first/last frames."""
    if hasattr(frames, "tolist"):
        frames = frames.tolist()
    if not isinstance(frames, (list, tuple)) or len(frames) < 2:
        raise ValueError("frames must contain at least two HxWxC frames")

    height = len(frames[0])
    if height < 1:
        raise ValueError("frames must not be empty")
    width = len(frames[0][0]) if frames[0] else 0
    if width < 1:
        raise ValueError("frames must not be empty")
    channels = len(frames[0][0][0]) if frames[0][0] else 0
    if channels not in (1, 3, 4):
        raise ValueError("frames must contain 1, 3, or 4 channels")

    grayscale = []
    for frame in frames:
        if len(frame) != height:
            raise ValueError("all frames must have equal dimensions")
        gray_frame = []
        for row in frame:
            if len(row) != width:
                raise ValueError("all frames must have equal dimensions")
            gray_row = []
            for pixel in row:
                if len(pixel) != channels:
                    raise ValueError("all pixels must have the same channel count")
                gray_row.append(sum(float(v) for v in pixel[:3]) / min(channels, 3))
            gray_frame.append(gray_row)
        grayscale.append(gray_frame)

    pair_means = []
    pair_moving_fractions = []
    pixel_count = height * width
    for previous, current in zip(grayscale, grayscale[1:]):
        total_delta = 0.0
        moving_pixels = 0
        for y in range(height):
            for x in range(width):
                delta = abs(current[y][x] - previous[y][x])
                total_delta += delta
                if delta >= pixel_delta_threshold:
                    moving_pixels += 1
        pair_means.append(total_delta / pixel_count)
        pair_moving_fractions.append(moving_pixels / pixel_count)

    active_pairs = sum(f >= active_pair_fraction_threshold for f in pair_moving_fractions)
    mean_moving_fraction = statistics.fmean(pair_moving_fractions)
    active_pair_fraction = active_pairs / len(pair_moving_fractions)
    return {
        "frame_count": len(frames),
        "mean_abs_frame_difference": round(statistics.fmean(pair_means), 4),
        "median_abs_frame_difference": round(statistics.median(pair_means), 4),
        "mean_moving_pixel_fraction": round(mean_moving_fraction, 6),
        "active_pair_fraction": round(active_pair_fraction, 6),
        "pixel_delta_threshold": float(pixel_delta_threshold),
        "active_pair_fraction_threshold": float(active_pair_fraction_threshold),
        "near_static_signal": bool(active_pair_fraction < 0.10 or mean_moving_fraction < 0.005),
        "interpretation": "diagnostic_only_requires_visual_review",
    }
