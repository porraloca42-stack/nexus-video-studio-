"""Serverless LTX image-to-video worker deployed on Modal.

Uses the official LTX-Video 0.9.8 distilled multi-scale pipeline:
7-step low-resolution pass, 2x latent upscaler, 3-step refinement.
"""
import io
import random
import tempfile
import time
from pathlib import Path

import modal

from nexus.ltx_motion_metrics import measure_temporal_motion

from nexus.ltx_config import (
    DECODE_NOISE_SCALE,
    DECODE_TIMESTEP,
    FPS,
    GPU_COST_BUDGET_USD,
    GPU_RATE_USD_PER_SECOND,
    GPU_TYPE,
    HEIGHT,
    IMAGE_COND_NOISE_SCALE,
    INFERENCE_STEP_COUNT,
    MODEL_CHECKPOINT,
    MODEL_CODE_REVISION,
    MODEL_ID,
    MODEL_NAME,
    MODEL_REVISION,
    SCALEDOWN_WINDOW_SECONDS,
    SPATIAL_UPSCALER,
    WIDTH,
    build_pipeline_config,
)

APP_NAME = "nexus-video-i2v"
MODEL_CACHE = "/models"
model_cache = modal.Volume.from_name("nexus-ltx-model-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git", "ffmpeg")
    .uv_pip_install(
        "accelerate==1.4.0",
        "av==14.2.0",
        "diffusers==0.32.2",
        "einops==0.8.1",
        "huggingface-hub==0.30.2",
        "imageio[ffmpeg]==2.37.0",
        "numpy==2.2.3",
        "pillow==11.1.0",
        "pyyaml==6.0.2",
        "safetensors==0.5.3",
        "sentencepiece==0.2.0",
        "timm==1.0.15",
        "torch==2.6.0",
        "torchvision==0.21.0",
        "transformers==4.49.0",
    )
    .uv_pip_install(
        f"git+https://github.com/Lightricks/LTX-Video.git@{MODEL_CODE_REVISION}"
    )
    .env({"HF_XET_HIGH_PERFORMANCE": "1", "HF_HUB_CACHE": MODEL_CACHE})
    .add_local_python_source("nexus")
)

MINUTES = 60


def frames_for_duration(seconds):
    """LTX frame count must be 8*n+1; return the closest supported duration."""
    target = max(2.0, min(5.0, float(seconds or 3.0)))
    units = max(6, round((target * FPS - 1) / 8))
    return units * 8 + 1


app = modal.App(APP_NAME)


@app.cls(
    image=image,
    gpu=GPU_TYPE,
    timeout=45 * MINUTES,
    scaledown_window=SCALEDOWN_WINDOW_SECONDS,
    volumes={MODEL_CACHE: model_cache},
)
class Inference:
    @modal.enter()
    def load_pipeline(self):
        load_started = time.monotonic()
        import torch
        from huggingface_hub import hf_hub_download
        from ltx_video.inference import create_latent_upsampler, create_ltx_video_pipeline
        from ltx_video.pipelines.pipeline_ltx_video import LTXMultiScalePipeline
        from ltx_video.utils.skip_layer_strategy import SkipLayerStrategy

        self.torch = torch
        checkpoint_path = hf_hub_download(
            repo_id=MODEL_ID,
            filename=MODEL_CHECKPOINT,
            revision=MODEL_REVISION,
            cache_dir=MODEL_CACHE,
        )
        upscaler_path = hf_hub_download(
            repo_id=MODEL_ID,
            filename=SPATIAL_UPSCALER,
            revision=MODEL_REVISION,
            cache_dir=MODEL_CACHE,
        )
        config = build_pipeline_config()
        stg_mode = config.pop("stg_mode", "attention_values")
        self.pipeline_config = config
        self.skip_layer_strategy = SkipLayerStrategy.AttentionValues
        if stg_mode != "attention_values":
            raise ValueError(f"Perfil LTX contém stg_mode inesperado: {stg_mode}")

        base_pipeline = create_ltx_video_pipeline(
            ckpt_path=checkpoint_path,
            precision="bfloat16",
            text_encoder_model_name_or_path="PixArt-alpha/PixArt-XL-2-1024-MS",
            sampler="from_checkpoint",
            device="cuda",
            enhance_prompt=False,
        )
        latent_upsampler = create_latent_upsampler(
            latent_upsampler_model_path=upscaler_path,
            device=base_pipeline.device,
        )
        self.pipe = LTXMultiScalePipeline(
            base_pipeline,
            latent_upsampler=latent_upsampler,
        )
        # Modal Volumes require an explicit commit to persist newly downloaded weights.
        model_cache.commit()
        self.model_load_seconds = round(time.monotonic() - load_started, 3)
        load_gpu_cost = (self.model_load_seconds + SCALEDOWN_WINDOW_SECONDS) * GPU_RATE_USD_PER_SECOND
        if load_gpu_cost >= GPU_COST_BUDGET_USD:
            raise RuntimeError(
                f"LTX abortado para proteger o orçamento: carregamento estimado em "
                + f"{load_gpu_cost:.3f} USD de GPU antes de gerar cenas."
            )
        self.gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "unknown"
        print({
            "event": "ltx_model_ready",
            "model": MODEL_NAME,
            "model_revision": MODEL_REVISION,
            "model_code_revision": MODEL_CODE_REVISION,
            "model_load_seconds": self.model_load_seconds,
            "gpu_name": self.gpu_name,
            "width": WIDTH,
            "height": HEIGHT,
            "fps": FPS,
            "first_pass_steps": 7,
            "second_pass_steps": 3,
            "prompt_enhancement": False,
        })

    @modal.method()
    def run_batch(self, scenes):
        """Animate approved keyframes using the official LTX multi-scale I2V pipeline."""
        import imageio.v2 as imageio
        import numpy as np
        from PIL import Image, ImageOps
        from ltx_video.inference import calculate_padding, prepare_conditioning

        results = []
        batch_started = time.monotonic()

        def estimated_gpu_cost():
            active_seconds = (
                self.model_load_seconds
                + (time.monotonic() - batch_started)
                + SCALEDOWN_WINDOW_SECONDS
            )
            return active_seconds * GPU_RATE_USD_PER_SECOND

        height_padded = ((HEIGHT - 1) // 32 + 1) * 32
        width_padded = ((WIDTH - 1) // 32 + 1) * 32
        padding = calculate_padding(HEIGHT, WIDTH, height_padded, width_padded)

        for index, item in enumerate(scenes, start=1):
            if estimated_gpu_cost() >= GPU_COST_BUDGET_USD:
                raise RuntimeError(
                    f"LTX interrompido para proteger o orçamento de {GPU_COST_BUDGET_USD:.2f} USD. "
                    + f"{index - 1} cenas concluídas; GPU estimada em "
                    + f"{estimated_gpu_cost():.3f} USD."
                )
            image_bytes = item.get("image_bytes")
            prompt = str(item.get("prompt") or "").strip()
            if not image_bytes or not prompt:
                raise ValueError(f"Cena {index}: imagem ou prompt de movimento ausente.")

            source = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            source = ImageOps.fit(source, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
            duration = max(2.0, min(5.0, float(item.get("duration_seconds") or 3.0)))
            frame_count = frames_for_duration(duration)
            frame_count_padded = ((frame_count - 2) // 8 + 1) * 8 + 1
            seed = int(item.get("seed") or random.randint(1, 2**31 - 1))

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
                conditioning_path = Path(handle.name)
            source.save(conditioning_path)
            try:
                conditioning_items = prepare_conditioning(
                    conditioning_media_paths=[str(conditioning_path)],
                    conditioning_strengths=[1.0],
                    conditioning_start_frames=[0],
                    height=HEIGHT,
                    width=WIDTH,
                    num_frames=frame_count_padded,
                    padding=padding,
                    pipeline=self.pipe,
                )
                generator = self.torch.Generator(device="cuda").manual_seed(seed)
                started = time.monotonic()
                output = self.pipe(
                    **self.pipeline_config,
                    skip_layer_strategy=self.skip_layer_strategy,
                    generator=generator,
                    output_type="pt",
                    callback_on_step_end=None,
                    height=height_padded,
                    width=width_padded,
                    num_frames=frame_count_padded,
                    frame_rate=FPS,
                    prompt=prompt,
                    negative_prompt=(
                        "worst quality, inconsistent motion, blurry, jittery, distorted, "
                        "morphing face, extra limbs, changing identity, flicker, text, watermark"
                    ),
                    media_items=None,
                    conditioning_items=conditioning_items,
                    is_video=True,
                    vae_per_channel_normalize=True,
                    image_cond_noise_scale=IMAGE_COND_NOISE_SCALE,
                    mixed_precision=False,
                    offload_to_cpu=False,
                    device="cuda",
                    enhance_prompt=False,
                ).images
                inference_seconds = round(time.monotonic() - started, 3)
            finally:
                conditioning_path.unlink(missing_ok=True)

            video_frames = output[0].permute(1, 2, 3, 0).cpu().float().numpy()
            video_frames = np.clip(video_frames * 255.0, 0, 255).astype(np.uint8)
            motion_metrics = measure_temporal_motion(video_frames)
            output_path = Path(f"/tmp/nexus-scene-{index:02d}-{seed}.mp4")
            with imageio.get_writer(str(output_path), fps=FPS, codec="libx264") as writer:
                for frame in video_frames:
                    writer.append_data(frame)
            video_bytes = output_path.read_bytes()
            output_path.unlink(missing_ok=True)

            results.append({
                "scene_index": index,
                "video_bytes": video_bytes,
                "frames": frame_count_padded,
                "fps": FPS,
                "duration_seconds": frame_count_padded / FPS,
                "inference_seconds": inference_seconds,
                "seed": seed,
                "model": MODEL_NAME,
                "model_revision": MODEL_REVISION,
                "model_code_revision": MODEL_CODE_REVISION,
                "width": WIDTH,
                "height": HEIGHT,
                "model_load_seconds": self.model_load_seconds,
                "batch_wall_seconds": round(time.monotonic() - batch_started, 3),
                "gpu_name": self.gpu_name,
                "num_inference_steps": INFERENCE_STEP_COUNT,
                "first_pass_steps": 7,
                "second_pass_steps": 3,
                "guidance_scale": 1.0,
                "decode_timestep": DECODE_TIMESTEP,
                "decode_noise_scale": DECODE_NOISE_SCALE,
                "image_cond_noise_scale": IMAGE_COND_NOISE_SCALE,
                "pipeline_type": "multi-scale",
                "estimated_gpu_cost_usd": round(estimated_gpu_cost(), 4),
                "gpu_cost_budget_usd": GPU_COST_BUDGET_USD,
                "motion_metrics": motion_metrics,
            })
            if estimated_gpu_cost() >= GPU_COST_BUDGET_USD:
                raise RuntimeError(
                    f"LTX interrompido após a cena {index} para proteger o orçamento. "
                    + f"GPU estimada em {estimated_gpu_cost():.3f} USD."
                )
            self.torch.cuda.empty_cache()
        return results
