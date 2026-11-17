"""Serverless LTX image-to-video worker deployed on Modal.

Deploy with: modal deploy modal_worker.py
The GPU is loaded once per container and scaled to zero after 60 seconds idle.
"""
import io
import random
import time
from pathlib import Path

import modal

APP_NAME = "nexus-video-i2v"
MODEL_ID = "Lightricks/LTX-Video"
MODEL_REVISION = "a6d59ee37c13c58261aa79027d3e41cd41960925"
MODEL_CACHE = "/models"
model_cache = modal.Volume.from_name("nexus-ltx-model-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("python3-opencv")
    .uv_pip_install(
        "accelerate==1.4.0",
        "diffusers==0.32.2",
        "huggingface-hub==0.36.0",
        "imageio==2.37.0",
        "imageio-ffmpeg==0.6.0",
        "opencv-python==4.11.0.86",
        "pillow==11.1.0",
        "sentencepiece==0.2.0",
        "torch==2.6.0",
        "torchvision==0.21.0",
        "transformers==4.49.0",
    )
    .env({"HF_XET_HIGH_PERFORMANCE": "1", "HF_HUB_CACHE": MODEL_CACHE})
)

MINUTES = 60
FPS = 24
WIDTH = 512
HEIGHT = 896


def frames_for_duration(seconds):
    """LTX frame count must be 8*n+1; return the closest supported duration."""
    target = max(2.0, min(5.0, float(seconds or 3.0)))
    units = max(6, round((target * FPS - 1) / 8))
    return units * 8 + 1


app = modal.App(APP_NAME)


@app.cls(
    image=image,
    gpu="H100",
    timeout=45 * MINUTES,
    scaledown_window=60,
    volumes={MODEL_CACHE: model_cache},
)
class Inference:
    @modal.enter()
    def load_pipeline(self):
        load_started = time.monotonic()
        import torch
        import diffusers

        self.torch = torch
        self.diffusers = diffusers
        self.pipe = diffusers.LTXImageToVideoPipeline.from_pretrained(
            MODEL_ID,
            revision=MODEL_REVISION,
            torch_dtype=torch.bfloat16,
        ).to("cuda")
        # Modal Volumes require an explicit commit to persist newly downloaded weights.
        model_cache.commit()
        self.model_load_seconds = round(time.monotonic() - load_started, 3)
        self.gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "unknown"
        print({"event": "ltx_model_ready", "model": MODEL_ID, "revision": MODEL_REVISION,
               "model_load_seconds": self.model_load_seconds, "gpu_name": self.gpu_name,
               "width": WIDTH, "height": HEIGHT, "fps": FPS})

    @modal.method()
    def run_batch(self, scenes):
        """Animate a batch of approved scene keyframes; returns MP4 bytes per scene."""
        from PIL import Image, ImageOps

        results = []
        batch_started = time.monotonic()
        for index, item in enumerate(scenes, start=1):
            image_bytes = item.get("image_bytes")
            prompt = str(item.get("prompt") or "").strip()
            if not image_bytes or not prompt:
                raise ValueError(f"Cena {index}: imagem ou prompt de movimento ausente.")

            source = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            source = ImageOps.fit(source, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
            duration = max(2.0, min(5.0, float(item.get("duration_seconds") or 3.0)))
            frame_count = frames_for_duration(duration)
            seed = int(item.get("seed") or random.randint(1, 2**31 - 1))
            self.torch.manual_seed(seed)
            started = time.monotonic()

            frames = self.pipe(
                image=source,
                prompt=prompt,
                negative_prompt=(
                    "worst quality, inconsistent motion, blurry, jittery, distorted, "
                    "morphing face, extra limbs, changing identity, flicker, text, watermark"
                ),
                width=WIDTH,
                height=HEIGHT,
                num_frames=frame_count,
                frame_rate=FPS,
                num_inference_steps=50,
                guidance_scale=3.0,
            ).frames[0]

            output_path = Path(f"/tmp/nexus-scene-{index:02d}-{seed}.mp4")
            self.diffusers.utils.export_to_video(frames, str(output_path), fps=FPS)
            video_bytes = output_path.read_bytes()
            output_path.unlink(missing_ok=True)
            results.append({
                "scene_index": index,
                "video_bytes": video_bytes,
                "frames": frame_count,
                "fps": FPS,
                "duration_seconds": frame_count / FPS,
                "inference_seconds": round(time.monotonic() - started, 3),
                "seed": seed,
                "model": MODEL_ID,
                "model_revision": MODEL_REVISION,
                "width": WIDTH,
                "height": HEIGHT,
                "model_load_seconds": self.model_load_seconds,
                "batch_wall_seconds": round(time.monotonic() - batch_started, 3),
                "gpu_name": self.gpu_name,
                "num_inference_steps": 50,
                "guidance_scale": 3.0,
            })
            self.torch.cuda.empty_cache()
        return results
