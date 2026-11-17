"""Render and inspect a deterministic Remotion multitrack fixture.

This is a CPU-only integration test. It uses generated tones, not external APIs,
paid media, production assets, or GPU inference.
"""
import json
import math
import re
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

from PIL import Image

from nexus.remotion_renderer import build_remotion_manifest


ROOT = Path(__file__).resolve().parents[1]
REMOTION = ROOT / "remotion"
JOB_ID = "synthetic-validation"
OUTPUT = REMOTION / "out" / "synthetic-validation.mp4"
FPS = 30
DURATION = 4.0
SAMPLE_RATE = 48000


def run(command, cwd=None):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(map(str, command))}\n"
            f"{(result.stderr or result.stdout)[-5000:]}"
        )
    return result


def write_tone(path, frequency, amplitude, seconds):
    frames = bytearray()
    count = int(SAMPLE_RATE * seconds)
    for index in range(count):
        sample = int(32767 * amplitude * math.sin(2 * math.pi * frequency * index / SAMPLE_RATE))
        frames.extend(struct.pack("<h", sample))
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(SAMPLE_RATE)
        audio.writeframes(frames)


def mean_volume(path, start, duration, band):
    low, high = band
    result = run([
        "ffmpeg", "-hide_banner", "-nostats", "-ss", str(start), "-t", str(duration),
        "-i", str(path), "-af",
        f"highpass=f={low},lowpass=f={high},volumedetect",
        "-f", "null", "-"
    ])
    match = re.search(r"mean_volume:\s*(-?inf|-?\d+(?:\.\d+)?)\s*dB", result.stderr)
    if not match:
        raise AssertionError(f"Could not read mean volume from FFmpeg:\n{result.stderr[-2000:]}")
    return float("-inf") if match.group(1) == "-inf" else float(match.group(1))


def extract_frame(path, seconds, target):
    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", str(seconds),
        "-i", str(path), "-frames:v", "1", "-vf", "scale=720:1280", str(target)
    ])
    if not target.is_file() or target.stat().st_size < 1000:
        raise AssertionError(f"Missing or empty rendered frame at {seconds}s")


def gold_caption_pixels(path):
    image = Image.open(path).convert("RGB").crop((20, 900, 700, 1200))
    count = 0
    for red, green, blue in image.getdata():
        if red > 220 and green > 150 and blue < 200:
            count += 1
    return count


def main():
    REMOTION.mkdir(exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nexus-remotion-fixture-") as temp:
        fixture = Path(temp)
        narration = fixture / "narration.wav"
        music = fixture / "music.wav"
        sfx = fixture / "impact.wav"
        write_tone(narration, 440, 0.07, DURATION)
        write_tone(music, 220, 0.14, DURATION)
        write_tone(sfx, 880, 0.22, 0.6)

        plan = {
            "seo": {"title": "NEXUS synthetic multitrack validation"},
            "music_audio_path": str(music),
            "music_volume": 0.35,
            "scenes": [{
                "id": "synthetic-scene",
                "duration_seconds": DURATION,
                "voiceover": "NEXUS valida legendas, efeitos e mixagem.",
            }],
            "edit_timeline": {
                "caption_events": [{
                    "id": "caption-validation",
                    "start_seconds": 0.5,
                    "end_seconds": 2.1,
                    "text": "NEXUS valida",
                    "position": "bottom",
                    "words": [
                        {"text": "NEXUS", "start_seconds": 0.5, "end_seconds": 1.2},
                        {"text": "valida", "start_seconds": 1.2, "end_seconds": 2.0},
                    ],
                }],
                "sfx_events": [{
                    "id": "sfx-validation",
                    "asset_path": str(sfx),
                    "start_seconds": 1.0,
                    "duration_seconds": 0.6,
                    "volume": 0.5,
                }],
                "audio_mix_events": [{
                    "start_seconds": 0.8,
                    "end_seconds": 2.2,
                    "music_volume": 0.05,
                    "fade_in_seconds": 0.2,
                    "fade_out_seconds": 0.2,
                }],
            },
        }
        manifest_path, manifest = build_remotion_manifest(
            plan, [], narration, REMOTION / "public", job_id=JOB_ID
        )
        assert manifest["durationInFrames"] == int(DURATION * FPS)
        assert len(manifest["captionEvents"]) == 1
        assert len(manifest["soundEffects"]) == 1
        assert len(manifest["audioMixEvents"]) == 1

    run([
        "npx", "remotion", "render", "src/index.ts", "NexusFromManifest",
        str(OUTPUT), f"--props={manifest_path.relative_to(REMOTION).as_posix()}",
        "--codec=h264", "--pixel-format=yuv420p", "--audio-codec=aac",
        "--concurrency=2", "--log=error",
    ], cwd=REMOTION)

    probe = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(OUTPUT)
    ])
    duration = float(json.loads(probe.stdout)["format"]["duration"])
    if abs(duration - DURATION) > 0.15:
        raise AssertionError(f"Rendered duration {duration:.3f}s != {DURATION:.3f}s")

    frames = {}
    for label, seconds in (("word_one", 0.8), ("word_two", 1.5), ("caption_off", 2.7)):
        frame_path = fixture / f"{label}.png"
        extract_frame(OUTPUT, seconds, frame_path)
        frames[label] = gold_caption_pixels(frame_path)
    if frames["word_one"] < frames["caption_off"] + 20:
        raise AssertionError(f"First word highlight not visible: {frames}")
    if frames["word_two"] < frames["caption_off"] + 20:
        raise AssertionError(f"Second word highlight not visible: {frames}")

    music_before = mean_volume(OUTPUT, 0.25, 0.35, (190, 250))
    music_ducked = mean_volume(OUTPUT, 1.2, 0.35, (190, 250))
    music_after = mean_volume(OUTPUT, 2.65, 0.35, (190, 250))
    if music_before - music_ducked < 8:
        raise AssertionError(
            f"Music ducking too weak: before={music_before:.1f}dB, ducked={music_ducked:.1f}dB"
        )
    if abs(music_before - music_after) > 5:
        raise AssertionError(
            f"Music did not recover after ducking: before={music_before:.1f}dB, after={music_after:.1f}dB"
        )

    sfx_before = mean_volume(OUTPUT, 0.25, 0.3, (760, 1000))
    sfx_active = mean_volume(OUTPUT, 1.15, 0.3, (760, 1000))
    if sfx_active - sfx_before < 10:
        raise AssertionError(
            f"SFX not audible in its scheduled window: before={sfx_before:.1f}dB, active={sfx_active:.1f}dB"
        )

    print(json.dumps({
        "status": "passed",
        "output": str(OUTPUT),
        "duration_seconds": round(duration, 3),
        "caption_gold_pixels": frames,
        "music_mean_volume_db": {
            "before": round(music_before, 1),
            "ducked": round(music_ducked, 1),
            "after": round(music_after, 1),
        },
        "sfx_mean_volume_db": {
            "before": round(sfx_before, 1),
            "active": round(sfx_active, 1),
        },
    }, indent=2))


if __name__ == "__main__":
    main()
