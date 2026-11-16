"""Client adapter for the NEXUS Modal image-to-video service."""
from pathlib import Path


class ModalVideoError(RuntimeError):
    pass


def build_motion_prompt(scene):
    """Prefer explicit motion direction; otherwise derive a conservative prompt."""
    explicit = str(
        scene.get("video_motion_prompt")
        or scene.get("motion_prompt")
        or scene.get("prompt_movimento_ingles")
        or ""
    ).strip()
    if explicit:
        return explicit[:1800]

    image_prompt = str(scene.get("image_prompt") or "").strip()
    visual_action = str(scene.get("visual_action") or "").strip()
    direction = scene.get("scene_direction") or {}
    camera = direction.get("camera") or {}
    move = str(camera.get("move") or scene.get("camera_motion") or "subtle push-in")
    motion_events = scene.get("motion_events") or []
    events = "; ".join(str(event).strip() for event in motion_events[:2] if str(event).strip())
    pieces = [
        image_prompt,
        "Animate the exact scene shown in the reference image.",
        f"Natural visible action: {visual_action}" if visual_action else "",
        f"Subtle cinematic camera movement: {move.replace('_', ' ')}.",
        f"Specific motion beats: {events}." if events else "",
        "Preserve the same subject identity, face, clothing, composition, environment, and visual style. "
        "Use physically plausible motion, stable anatomy, natural timing, and no cuts or scene changes.",
    ]
    return " ".join(piece for piece in pieces if piece)[:1800]


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
        payload.append({
            "image_bytes": image_path.read_bytes(),
            "prompt": build_motion_prompt(scene),
            "duration_seconds": duration,
        })

    if progress_callback:
        progress_callback(f"Enviando {len(payload)} cenas para animação no Modal (LTX-Video)...")
    try:
        if modal_cls is None:
            import modal
            modal_cls = modal.Cls
        inference = modal_cls.from_name("nexus-video-i2v", "Inference")()
        results = inference.run_batch.remote(payload)
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
        })
        if progress_callback:
            progress_callback(f"Cena {index}/{len(results)} animada e recebida do Modal.")
    return saved
