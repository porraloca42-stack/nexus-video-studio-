"""One-scene live NEXUS pipeline test: Cloudflare image -> Modal LTX -> Remotion MP4."""
import json
import os
import subprocess
from pathlib import Path

from nexus.cloudflare_images import generate_image
from nexus.modal_i2v import animate_scene_images
from nexus.remotion_renderer import render_video_remotion

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "nexus-live-pipeline-output"
JOB_ID = "live-pipeline-smoke"


def run(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=240)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout)[-4000:])
    return result.stdout


def probe(path):
    data = json.loads(run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_type,codec_name,width,height",
        "-of", "json", str(path)
    ]))
    return data


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    scene = {
        "id": "live-scene-01",
        "duration_seconds": 2.0,
        "voiceover": "A mudança começa quando você decide enxergar além do óbvio.",
        "image_prompt": (
            "Vertical cinematic photorealistic scene: a lone human silhouette standing "
            "on a dark mountain ridge at blue hour, looking toward a vast luminous cosmic "
            "nebula opening above the horizon, delicate stars, atmospheric clouds, subtle "
            "golden light breaking through, profound sense of wonder, realistic film still, "
            "high detail, no text, no logos, no watermark."
        ),
        "video_motion_prompt": (
            "Only the thin cloud layer drifts slowly from left to right across the sky. "
            "Keep the person, mountain, stars and camera completely still. "
            "One simple, continuous, physically plausible movement. No cuts."
        ),
        "scene_direction": {
            "camera": {"move": "push_in", "intensity": 0.35},
            "atmosphere": {"effect": "fog", "intensity": 0.2},
            "lighting": {"change": "light_sweep"},
            "transition": {"in": "fade", "out": "fade"}
        },
    }
    image = generate_image(
        scene["image_prompt"], OUT / "cloudflare-scene.png",
        steps=4, width=512, height=910
    )
    clips = animate_scene_images(
        [image], [scene], OUT / "motion",
        progress_callback=lambda message: print(message, flush=True)
    )
    clip = Path(clips[0]["path"])
    clip_meta = probe(clip)
    video_stream = next((s for s in clip_meta["streams"] if s["codec_type"] == "video"), None)
    if not video_stream or video_stream.get("width") != 384 or video_stream.get("height") != 672:
        raise RuntimeError(f"LTX low-cost clip has invalid video stream: {clip_meta}")

    # A neutral tone track exercises Remotion's audio muxing without requiring a voice API key.
    audio = OUT / "validation-tone.wav"
    run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        "sine=frequency=440:sample_rate=44100:duration=2.0",
        "-c:a", "pcm_s16le", str(audio)
    ])
    plan = {"seo": {"title": "NEXUS live pipeline validation"}, "scenes": [scene]}
    final = OUT / "nexus-live-pipeline.mp4"
    render_video_remotion(
        [{"path": str(clip)}], audio, final, plan,
        project_dir=ROOT / "remotion", job_id=JOB_ID
    )
    final_meta = probe(final)
    final_video = next((s for s in final_meta["streams"] if s["codec_type"] == "video"), None)
    final_audio = next((s for s in final_meta["streams"] if s["codec_type"] == "audio"), None)
    duration = float(final_meta["format"]["duration"])
    if not final_video or (final_video.get("width"), final_video.get("height")) != (720, 1280):
        raise RuntimeError(f"Remotion output is not 720x1280: {final_meta}")
    if not final_audio or final_audio.get("codec_name") != "aac":
        raise RuntimeError(f"Remotion output has no AAC audio: {final_meta}")
    if not 1.7 <= duration <= 2.4 or final.stat().st_size < 20_000:
        raise RuntimeError(f"Final MP4 failed duration/size validation: {final_meta}")

    report = {
        "status": "success",
        "pipeline": [
            "Cloudflare Workers AI FLUX.2 Klein",
            f"Modal LTX-Video ({clips[0].get('gpu_name') or 'GPU informada pelo worker'})",
            "Remotion",
        ],
        "image": {"model": image["model"], "bytes": image["bytes"], "width": 512, "height": 910},
        "ltx": {
            "profile": "low-cost-simple-motion",
            "target_width": 384,
            "target_height": 672,
            "gpu_budget_usd": 0.15,
            "model": clips[0]["model"],
            "gpu_name": clips[0].get("gpu_name"),
            "duration_seconds": clips[0]["duration_seconds"],
            "inference_seconds": clips[0]["inference_seconds"],
            "frames": clips[0]["frames"],
            "probe": clip_meta,
        },
        "remotion": {
            "duration_seconds": duration,
            "video": final_video,
            "audio": final_audio,
            "file_size_bytes": final.stat().st_size,
        },
        "audio_note": "Synthetic validation tone, not production narration. This test isolates the visual pipeline and Remotion muxing.",
    }
    (OUT / "pipeline-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
