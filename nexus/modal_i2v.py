"""Client adapter for the NEXUS Modal image-to-video service."""
from pathlib import Path
import time


class ModalVideoError(RuntimeError):
    pass


def build_motion_prompt(scene):
    """Require a dedicated action-first English I2V prompt; never recycle the still-image prompt."""
    explicit = str(
        scene.get("video_motion_prompt")
        or scene.get("motion_prompt")
        or scene.get("prompt_movimento_ingles")
        or ""
    ).strip()
    if len(explicit) < 40:
        raise ModalVideoError(
            "Prompt de movimento LTX ausente ou insuficiente. "
            "A cena foi bloqueada antes de consumir GPU; o prompt da imagem estática "
            "não será reutilizado como instrução de vídeo."
        )
    return explicit[:1800]


def animate_scene_images(generated_images, scenes, output_dir, *, modal_cls=None, progress_callback=None):
    """Send all scene keyframes in one Modal call and save returned MP4 clips."""
    if len(generated_images) != len(scenes) or not scenes:
        raise ModalVideoError("A quantidade de imagens precisa corresponder à quantidade de cenas.")
    payload = []
    for index, (asset, scene) in enumerate(zip(generated_images, scenes), start=1):
        image_path = Path(asset["path"])
        if not image_path.is_file():
            raise ModalVideoError(f"Imagem-base da cena {index} não encontrada.")
        duration = scene.get("duration_seconds") or scene.get("duration") or 3.0
        try:
            duration = float(duration)
        except (TypeError, ValueError) as exc:
            raise ModalVideoError(f"Duração inválida na cena {index}.") from exc
        if not 2.0 <= duration <= 5.0:
            raise ModalVideoError(f"Cena {index}: duração de {duration:g}s fora da faixa I2V de 2–5s.")
        motion_prompt = build_motion_prompt(scene)
        payload.append({
            "image_bytes": image_path.read_bytes(),
            "prompt": motion_prompt,
            "duration_seconds": duration,
        })

    if progress_callback:
        progress_callback(f"Enviando {len(payload)} cenas para animação no Modal (LTX-Video)...")
    try:
        if modal_cls is None:
            import modal
            modal_cls = modal.Cls
        inference = modal_cls.from_name("nexus-video-i2v", "Inference")()
        modal_call_started = time.monotonic()
        results = inference.run_batch.remote(payload)
        modal_call_wall_seconds = round(time.monotonic() - modal_call_started, 3)
    except Exception as exc:
        raise ModalVideoError(
            "Falha ao gerar movimento orgânico no Modal. O NEXUS interrompeu o render "
            "em vez de substituir silenciosamente os vídeos por imagens estáticas. "
            f"Detalhe: {str(exc)[:900]}"
        ) from exc

    if not isinstance(results, list) or len(results) != len(scenes):
        raise ModalVideoError("Modal retornou uma quantidade de clipes diferente da quantidade solicitada.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for index, result in enumerate(results, start=1):
        video_bytes = result.get("video_bytes") if isinstance(result, dict) else None
        if not isinstance(video_bytes, bytes) or len(video_bytes) < 10_000:
            raise ModalVideoError(f"Modal retornou um clipe inválido para a cena {index}.")
        destination = output_dir / f"scene_{index:02d}.mp4"
        destination.write_bytes(video_bytes)
        saved.append({
            "path": str(destination),
            "scene_index": index,
            "duration_seconds": result.get("duration_seconds"),
            "inference_seconds": result.get("inference_seconds"),
            "frames": result.get("frames"),
            "model": result.get("model", "Lightricks/LTX-Video"),
            "motion_prompt": payload[index - 1]["prompt"],
            "model_load_seconds": result.get("model_load_seconds"),
            "batch_wall_seconds": result.get("batch_wall_seconds"),
            "modal_call_wall_seconds": modal_call_wall_seconds,
            "gpu_name": result.get("gpu_name"),
            "num_inference_steps": result.get("num_inference_steps"),
        })
        if progress_callback:
            progress_callback(f"Cena {index}/{len(results)} animada e recebida do Modal.")
    return saved
