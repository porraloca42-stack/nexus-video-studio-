"""Pinned, budget-oriented LTX-Video 0.9.8 distilled multi-scale profile."""

MODEL_ID = "Lightricks/LTX-Video"
MODEL_REVISION = "main"
MODEL_CODE_REVISION = "50f0aef1297574a4b29acbdb874e3a363a6d5f2e"
MODEL_NAME = "LTX-Video 2B v0.9.8 distilled (multi-scale)"
MODEL_CHECKPOINT = "ltxv-2b-0.9.8-distilled.safetensors"
SPATIAL_UPSCALER = "ltxv-spatial-upscaler-0.9.8.safetensors"
GPU_TYPE = "L40S"
GPU_RATE_USD_PER_SECOND = 0.000542
GPU_COST_BUDGET_USD = 0.42  # Reserve 0.08 for CPU, memory and billing variance.
SCALEDOWN_WINDOW_SECONDS = 5

WIDTH = 512
HEIGHT = 896
FPS = 24
INFERENCE_STEP_COUNT = 10
GUIDANCE_SCALE = 1.0
DECODE_TIMESTEP = 0.05
DECODE_NOISE_SCALE = 0.025
IMAGE_COND_NOISE_SCALE = 0.025

PIPELINE_CONFIG = {
    "pipeline_type": "multi-scale",
    "checkpoint_path": MODEL_CHECKPOINT,
    "downscale_factor": 0.6666666,
    "spatial_upscaler_model_path": SPATIAL_UPSCALER,
    "stg_mode": "attention_values",
    "decode_timestep": DECODE_TIMESTEP,
    "decode_noise_scale": DECODE_NOISE_SCALE,
    "text_encoder_model_name_or_path": "PixArt-alpha/PixArt-XL-2-1024-MS",
    "precision": "bfloat16",
    "sampler": "from_checkpoint",
    # Gemini already writes the action-first prompt; avoid loading a second LLM stack.
    "prompt_enhancement_words_threshold": 0,
    "prompt_enhancer_image_caption_model_name_or_path": "MiaoshouAI/Florence-2-large-PromptGen-v2.0",
    "prompt_enhancer_llm_model_name_or_path": "unsloth/Llama-3.2-3B-Instruct",
    "stochastic_sampling": False,
    "first_pass": {
        "timesteps": [1.0000, 0.9937, 0.9875, 0.9812, 0.9750, 0.9094, 0.7250],
        "guidance_scale": 1,
        "stg_scale": 0,
        "rescaling_scale": 1,
        "skip_block_list": [42],
    },
    "second_pass": {
        "timesteps": [0.9094, 0.7250, 0.4219],
        "guidance_scale": 1,
        "stg_scale": 0,
        "rescaling_scale": 1,
        "skip_block_list": [42],
    },
}


def build_pipeline_config():
    """Return a fresh config because the official inference path removes stg_mode."""
    import copy

    return copy.deepcopy(PIPELINE_CONFIG)
