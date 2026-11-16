"""Cloudflare Workers AI image generation adapter.

This module is intentionally isolated from the Streamlit render flow until
credentials, model output, and the Remotion end-to-end pipeline are validated.
"""
import base64
import binascii
import json
import os
from pathlib import Path

import requests


DEFAULT_MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
VERTICAL_MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
API_URL = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"


class CloudflareAIError(RuntimeError):
    """Raised when Cloudflare Workers AI cannot produce a usable image."""


def generate_image(
    prompt,
    output_path,
    *,
    account_id=None,
    api_token=None,
    model=None,
    steps=4,
    width=512,
    height=910,
    timeout=180,
    session=None,
):
    """Generate one image and save it locally; returns its path and metadata."""
    account_id = account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID")
    api_token = api_token or os.getenv("CLOUDFLARE_API_TOKEN")
    model = model or os.getenv("CLOUDFLARE_IMAGE_MODEL", DEFAULT_MODEL)
    if not account_id or not api_token:
        raise CloudflareAIError(
            "Configure CLOUDFLARE_ACCOUNT_ID e CLOUDFLARE_API_TOKEN nos Secrets."
        )
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("O prompt da imagem não pode ficar vazio.")
    client = session or requests
    url = API_URL.format(account_id=account_id, model=model)
    headers = {"Authorization": f"Bearer {api_token}"}
    if model == VERTICAL_MODEL:
        if not 256 <= int(width) <= 1920 or not 256 <= int(height) <= 1920:
            raise ValueError("A resolução de imagem deve ficar entre 256 e 1920 pixels.")
        # FLUX.2 klein 4B requires multipart/form-data and has a fixed 4-step inference.
        response = client.post(
            url,
            headers=headers,
            files={
                "prompt": (None, prompt.strip()),
                "width": (None, str(int(width))),
                "height": (None, str(int(height))),
            },
            timeout=timeout,
        )
    else:
        if not 1 <= int(steps) <= 8:
            raise ValueError("FLUX.1-schnell aceita de 1 a 8 steps neste adaptador.")
        response = client.post(
            url,
            headers=headers,
            json={"prompt": prompt.strip(), "steps": int(steps)},
            timeout=timeout,
        )
    if response.status_code >= 400:
        detail = response.text[:1200]
        raise CloudflareAIError(
            f"Cloudflare Workers AI retornou HTTP {response.status_code}: {detail}"
        )

    content_type = response.headers.get("content-type", "").lower()
    image_bytes = None
    if "application/json" in content_type:
        try:
            payload = response.json()
            result = payload.get("result", payload)
            encoded = result.get("image") or result.get("image_base64")
            if encoded:
                encoded = encoded.split(",", 1)[-1] if encoded.startswith("data:") else encoded
                image_bytes = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError, AttributeError, binascii.Error) as exc:
            raise CloudflareAIError("Resposta JSON de imagem inválida do Cloudflare.") from exc
    else:
        image_bytes = response.content

    if not image_bytes:
        raise CloudflareAIError("Cloudflare não retornou bytes de imagem.")

    if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        extension = ".png"
    elif image_bytes.startswith(b"\xff\xd8\xff"):
        extension = ".jpg"
    elif image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        extension = ".webp"
    else:
        raise CloudflareAIError("A resposta do Cloudflare não é PNG, JPEG ou WebP válido.")

    destination = Path(output_path)
    if destination.suffix.lower() != extension and not (extension == ".jpg" and destination.suffix.lower() == ".jpeg"):
        destination = destination.with_suffix(extension)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(image_bytes)
    return {
        "path": str(destination),
        "model": model,
        "steps": 4 if model == VERTICAL_MODEL else int(steps),
        "width": int(width) if model == VERTICAL_MODEL else None,
        "height": int(height) if model == VERTICAL_MODEL else None,
        "bytes": len(image_bytes),
        "content_type": content_type or f"image/{extension.lstrip('.')}",
    }


def generate_scene_images(scenes, output_dir, *, steps=6, **kwargs):
    """Generate one image per scene from each scene's image_prompt field."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for index, scene in enumerate(scenes, start=1):
        prompt = scene.get("image_prompt") or scene.get("visual_action") or ""
        destination = output_dir / f"scene_{index:02d}.png"
        try:
            result = generate_image(prompt, destination, steps=steps, **kwargs)
        except CloudflareAIError as exc:
            # Workers AI may reject a generated output even when the request is valid.
            # Retry only moderation code 3030, once, with a conservative editorial framing.
            # The scene's subject and action remain in the prompt; no blocked detail is amplified.
            if '"code":3030' not in str(exc) and '"code": 3030' not in str(exc):
                raise
            safe_prompt = (
                "Create a non-graphic, non-sexual, fictional editorial cinematic image. "
                "Show the scene in a calm, respectful, non-threatening way; no nudity, "
                "gore, visible injuries, weapons in use, logos, or text. Preserve the "
                "setting, subject, and benign action described here: " + str(prompt).strip()
            )
            try:
                result = generate_image(safe_prompt, destination, steps=steps, **kwargs)
                result["moderation_retry"] = True
            except CloudflareAIError as retry_exc:
                raise CloudflareAIError(
                    f"Cloudflare bloqueou a imagem da cena {index} (código 3030), "
                    "inclusive após uma tentativa com enquadramento visual seguro. "
                    "Revise o image_prompt/visual_action dessa cena no planejamento."
                ) from retry_exc
        result["scene_index"] = index
        results.append(result)
    return results
