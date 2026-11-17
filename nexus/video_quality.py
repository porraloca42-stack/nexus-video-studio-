"""No-cost, FFmpeg-based freeze diagnostics for generated video clips.

This detects long periods with almost no pixel change. It is a technical
diagnostic only: it does not prove that the visible action matches the script.
"""
import re
import subprocess
from pathlib import Path


_FREEZE_EVENT = re.compile(
    r"lavfi\.freezedetect\.(freeze_start|freeze_end|freeze_duration):\s*([0-9.]+)"
)


def parse_freeze_intervals(stderr: str, duration_seconds: float) -> dict:
    """Convert FFmpeg freezedetect events into a bounded freeze-ratio report."""
    duration = max(0.0, float(duration_seconds or 0.0))
    intervals = []
    active_start = None

    for event, raw_value in _FREEZE_EVENT.findall(stderr or ""):
        value = min(duration, max(0.0, float(raw_value)))
        if event == "freeze_start":
            active_start = value
        elif event == "freeze_end" and active_start is not None:
            if value > active_start:
                intervals.append((active_start, value))
            active_start = None

    if active_start is not None and duration > active_start:
        intervals.append((active_start, duration))

    frozen_seconds = sum(end - start for start, end in intervals)
    longest_freeze = max((end - start for start, end in intervals), default=0.0)
    ratio = min(1.0, frozen_seconds / duration) if duration else 0.0
    return {
        "status": "analyzed",
        "duration_seconds": round(duration, 3),
        "frozen_seconds": round(frozen_seconds, 3),
        "freeze_ratio": round(ratio, 4),
        "longest_freeze_seconds": round(longest_freeze, 3),
        "freeze_intervals": [
            {"start": round(start, 3), "end": round(end, 3)}
            for start, end in intervals
        ],
        "diagnostic": "low_motion_warning" if ratio >= 0.4 else "no_long_freeze_detected",
        "method": "ffmpeg_freezedetect_n_minus_50dB_d_0_5s",
        "limitation": "Detecta congelamento visual; não avalia se a ação corresponde à narração.",
    }


def analyze_video_motion(video_path: str | Path, duration_seconds: float) -> dict:
    """Run FFmpeg's built-in freeze detector without external APIs or paid services."""
    path = Path(video_path)
    if not path.is_file():
        raise FileNotFoundError(f"Clipe não encontrado para análise de movimento: {path}")
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-i", str(path),
            "-vf", "freezedetect=n=-50dB:d=0.5",
            "-an", "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
        timeout=90,
    )
    if result.returncode:
        raise RuntimeError(
            "FFmpeg não conseguiu analisar congelamentos: "
            + (result.stderr or "")[-800:]
        )
    return parse_freeze_intervals(result.stderr, duration_seconds)
