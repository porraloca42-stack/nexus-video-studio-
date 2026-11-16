"""One-scene smoke test for the deployed NEXUS LTX worker."""
import json
import subprocess
from pathlib import Path

import modal
from PIL import Image, ImageDraw

APP_NAME = "nexus-video-i2v"
OUTPUT = Path("modal-smoke-output")
OUTPUT.mkdir(exist_ok=True)


def make_reference_image() -> bytes:
    image = Image.new("RGB", (512, 896))
    pixels = image.load()
    for y in range(image.height):
        t = y / image.height
        color = (int(8 + 30 * t), int(18 + 55 * t), int(45 + 75 * t))
        for x in range(image.width):
            pixels[x, y] = color
    draw = ImageDraw.Draw(image)
    # Minimal sunrise landscape: sufficient to validate image conditioning and MP4 export.
    draw.ellipse((335, 180, 435, 280), fill=(246, 177, 91))
    draw.polygon([(0, 560), (110, 390), (230, 575), (350, 420), (512, 590), (512, 896), (0, 896)], fill=(30, 52, 67))
    draw.polygon([(0, 700), (160, 560), (300, 730), (420, 600), (512, 690), (512, 896), (0, 896)], fill=(13, 31, 43))
    import io
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def main():
    inference = modal.Cls.from_name(APP_NAME, "Inference")()
    results = inference.run_batch.remote([{
        "image_bytes": make_reference_image(),
        "prompt": (
            "A cinematic sunrise over a dramatic mountain landscape. "
            "Thin clouds drift slowly across the sky, warm sunlight gradually "
            "brightens the mountain ridges, subtle atmospheric haze moves naturally. "
            "A very slow cinematic camera push forward. Preserve the exact landscape "
            "composition, stable geometry, physically plausible motion, no cuts."
        ),
        "duration_seconds": 2.0,
        "seed": 369,
    }])
    if not isinstance(results, list) or len(results) != 1:
        raise RuntimeError("Modal did not return exactly one scene.")
    video = results[0].get("video_bytes")
    if not isinstance(video, bytes) or len(video) < 10_000:
        raise RuntimeError("Modal returned an empty or invalid MP4 payload.")

    mp4 = OUTPUT / "ltx-smoke-test.mp4"
    mp4.write_bytes(video)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=codec_name,codec_type,width,height",
         "-of", "json", str(mp4)],
        capture_output=True, text=True, check=True,
    )
    metadata = json.loads(probe.stdout)
    video_stream = next((s for s in metadata["streams"] if s["codec_type"] == "video"), None)
    duration = float(metadata["format"]["duration"])
    if not video_stream or video_stream.get("width") != 512 or video_stream.get("height") != 896:
        raise RuntimeError(f"Unexpected video stream metadata: {metadata}")
    if not 1.5 <= duration <= 3.0:
        raise RuntimeError(f"Unexpected clip duration: {duration}")

    report = {
        "status": "success",
        "model": results[0].get("model"),
        "model_revision": results[0].get("model_revision"),
        "duration_seconds": duration,
        "inference_seconds": results[0].get("inference_seconds"),
        "frames": results[0].get("frames"),
        "fps": results[0].get("fps"),
        "width": video_stream["width"],
        "height": video_stream["height"],
        "codec": video_stream.get("codec_name"),
        "file_size_bytes": mp4.stat().st_size,
        "note": "Synthetic reference image; validates inference and MP4 export, not editorial image quality.",
    }
    (OUTPUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
