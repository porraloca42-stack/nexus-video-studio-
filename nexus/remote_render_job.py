"""Build a Cloudflare-image/Remotion video on an isolated GitHub Actions worker."""
import json
import os
import subprocess
from pathlib import Path

from nexus.audio import make_voice
from nexus.director import revise_narration_for_duration, _fit_scene_durations
from nexus.cloudflare_images import generate_scene_images
from nexus.modal_i2v import animate_scene_images
from nexus.remotion_renderer import render_video_remotion
from nexus.render_crypto import decrypt_compressed_text, decrypt_text, encrypt_bytes, encrypt_text


def generate_worker_narration(text, voice, output_path, fish_api_key="", fish_voice_id=""):
    """Generate narration with the selected Fish Audio voice; never substitute a system TTS voice."""
    return make_voice(
        text,
        voice,
        output_path,
        fish_api_key=fish_api_key or None,
        fish_voice_id=fish_voice_id or None,
        return_provider=True,
    )


def _measure_audio_duration(audio_path: Path) -> float:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True, timeout=60,
    )
    if probe.returncode:
        raise RuntimeError("Não foi possível medir a duração da narração no worker.")
    try:
        actual = float(probe.stdout.strip())
    except (TypeError, ValueError):
        raise RuntimeError("A Fish Audio retornou uma duração de narração inválida.") from None
    if actual <= 0:
        raise RuntimeError("A narração gerada está vazia ou tem duração inválida.")
    return actual


def _fit_narration_to_timeline(audio_path: Path, target: float, actual_duration=None) -> float:
    """Gently time-stretch narration audio to the Remotion timeline; no captions are produced."""
    actual = float(actual_duration) if actual_duration is not None else _measure_audio_duration(audio_path)
    if target <= 0 or actual <= 0:
        raise RuntimeError("Duração inválida para sincronização da narração.")
    ratio = actual / target
    if abs(ratio - 1.0) <= 0.02:
        return actual
    if not 0.85 <= ratio <= 1.15:
        raise RuntimeError(
            f"A narração ficou com {actual:.1f}s para uma meta de {target:.1f}s "
            "e excede a faixa segura de ajuste de 15%. Revise o texto narrado."
        )
    adjusted_audio = audio_path.with_name(f"{audio_path.stem}_synced{audio_path.suffix}")
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(audio_path), "-filter:a", f"atempo={ratio:.6f}",
         "-vn", str(adjusted_audio)],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode or not adjusted_audio.exists():
        raise RuntimeError("Falha ao sincronizar a duração da narração: " + result.stderr[-1200:])
    audio_path.unlink(missing_ok=True)
    adjusted_audio.replace(audio_path)
    final_probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True, timeout=60,
    )
    if final_probe.returncode:
        raise RuntimeError("Não foi possível validar a narração sincronizada.")
    return float(final_probe.stdout.strip())


def main(project_root=None):
    raw = os.environ.get("NEXUS_MANIFEST_ENCRYPTED", "")
    encrypted_fish = os.environ.get("NEXUS_FISH_CREDENTIALS_ENCRYPTED", "")
    encryption_secret = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not raw or not encryption_secret:
        raise RuntimeError("Manifesto criptografado ou segredo de criptografia ausente.")
    plan = json.loads(decrypt_compressed_text(raw, encryption_secret))
    fish_credentials = {"api_key": "", "voice_id": ""}
    if encrypted_fish:
        fish_credentials.update(json.loads(decrypt_text(encrypted_fish, encryption_secret)))
    scenes = plan.get("scenes") or []
    if not scenes:
        raise RuntimeError("O manifesto não contém cenas.")
    job_id = os.environ.get("NEXUS_JOB_ID", "nexus-job")
    voice = os.environ.get("NEXUS_VOICE", "")
    root = Path(project_root or Path(__file__).resolve().parents[1])
    work = root / "worker_output" / job_id
    work.mkdir(parents=True, exist_ok=True)

    # The selected duration is an editorial reference; the hard ceiling is +10s.
    # Fish Audio is the source of truth for runtime. Never stretch or pad narration.
    narration = " ".join(str(scene.get("voiceover", "")).strip() for scene in scenes).strip()
    if not narration:
        raise RuntimeError("Narração vazia.")
    requested_duration = float(plan.get("requested_duration_seconds") or sum(
        float(scene.get("duration_seconds") or scene.get("duration") or 0)
        for scene in scenes
    ))
    maximum_duration = float(plan.get("maximum_duration_seconds") or (requested_duration + 10.0))
    if requested_duration <= 0 or maximum_duration < requested_duration:
        raise RuntimeError("A janela de duração do storyboard é inválida.")

    audio_path, narration_provider = generate_worker_narration(
        narration,
        voice,
        work / "narration.mp3",
        fish_api_key=fish_credentials.get("api_key", ""),
        fish_voice_id=fish_credentials.get("voice_id", ""),
    )
    audio_path = Path(audio_path)
    actual_audio_duration = _measure_audio_duration(audio_path)

    # Only edit if the real voice exceeds the allowed ceiling. The editor may
    # remove redundancy, but must never expand/pad the narration to hit a target.
    if actual_audio_duration > maximum_duration + 0.75:
        gemini_api_key = fish_credentials.get("gemini_api_key", "")
        if not gemini_api_key:
            raise RuntimeError(
                f"A narração natural ficou com {actual_audio_duration:.1f}s, acima do teto "
                f"de {maximum_duration:.0f}s. Nenhuma imagem foi gerada; configure o Gemini "
                "para permitir uma edição de contenção sem alterar a mensagem."
            )
        print(
            f"Narração acima do teto editorial ({actual_audio_duration:.1f}s / "
            f"{maximum_duration:.1f}s). Tentando uma única edição de contenção."
        )
        style = str(fish_credentials.get("style") or plan.get("style_lock") or "")
        topic = str(fish_credentials.get("topic") or plan.get("topic") or "")
        plan = revise_narration_for_duration(
            plan, maximum_duration, actual_audio_duration, topic, style,
            lambda name, default="": gemini_api_key if name == "GEMINI_API_KEY" else default,
        )
        scenes = plan.get("scenes") or []
        narration = " ".join(str(scene.get("voiceover", "")).strip() for scene in scenes).strip()
        audio_path.unlink(missing_ok=True)
        audio_path, narration_provider = generate_worker_narration(
            narration,
            voice,
            work / "narration.mp3",
            fish_api_key=fish_credentials.get("api_key", ""),
            fish_voice_id=fish_credentials.get("voice_id", ""),
        )
        audio_path = Path(audio_path)
        actual_audio_duration = _measure_audio_duration(audio_path)
        if actual_audio_duration > maximum_duration + 0.75:
            raise RuntimeError(
                f"Mesmo após a edição editorial, a narração ficou com {actual_audio_duration:.1f}s, "
                f"acima do teto de {maximum_duration:.0f}s. O trabalho foi interrompido antes "
                "da geração de imagens para evitar custo desnecessário."
            )

    # Scene boundaries follow the final narration's measured duration and each
    # scene's word share. Audio remains at its original natural speaking rate.
    fitted_durations = _fit_scene_durations(scenes, actual_audio_duration)
    plan["requested_duration_seconds"] = requested_duration
    plan["maximum_duration_seconds"] = maximum_duration
    plan["actual_duration_seconds"] = round(actual_audio_duration, 3)
    plan["duration_adjustment"] = {
        **(plan.get("duration_adjustment") or {}),
        "requested_seconds": requested_duration,
        "maximum_seconds": maximum_duration,
        "actual_narration_seconds": round(actual_audio_duration, 3),
        "scene_durations": fitted_durations,
        "timing_source": "measured_fish_audio_without_time_stretch",
    }
    expected_duration = actual_audio_duration
    narration_duration = actual_audio_duration

    generated = generate_scene_images(
        scenes,
        work / "images",
        steps=int(os.environ.get("CLOUDFLARE_IMAGE_STEPS", "4")),
        visual_continuity=plan.get("visual_continuity"),
    )
    media = []
    for item in generated:
        image_path = Path(item["path"])
        if image_path.stat().st_size < 10_000:
            raise RuntimeError(f"Imagem gerada muito pequena para uso editorial: cena {item.get('scene_index')}.")
        image_probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "json", str(image_path)],
            capture_output=True, text=True, timeout=45,
        )
        if image_probe.returncode:
            raise RuntimeError(f"Imagem da cena {item.get('scene_index')} não passou no FFprobe.")
        image_streams = json.loads(image_probe.stdout).get("streams", [])
        image_size = image_streams[0] if image_streams else {}
        width = int(image_size.get("width") or 0)
        height = int(image_size.get("height") or 0)
        if width < 1 or height < 1:
            raise RuntimeError(f"Imagem da cena {item.get('scene_index')} não informou dimensões válidas.")
        if width != 512 or height != 910:
            normalized_path = image_path.with_name(f"{image_path.stem}_vertical{image_path.suffix}")
            normalize = subprocess.run(
                ["ffmpeg", "-y", "-i", str(image_path), "-vf", "scale=512:910:flags=lanczos",
                 "-frames:v", "1", str(normalized_path)],
                capture_output=True, text=True, timeout=90,
            )
            if normalize.returncode or not normalized_path.exists():
                raise RuntimeError(
                    f"Não foi possível normalizar a imagem da cena {item.get('scene_index')} "
                    f"de {width}×{height} para 512×910: {normalize.stderr[-1200:]}"
                )
            image_path = normalized_path
        media.append({"path": str(image_path)})

    # Every approved keyframe is animated into a native MP4 clip on Modal.
    # A Modal failure is fatal here: never silently ship a static-image slideshow.
    motion_clips = animate_scene_images(generated, scenes, work / "motion")
    animated_media = []
    for index, clip in enumerate(motion_clips, start=1):
        clip_path = Path(clip["path"])
        clip_probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,width,height", "-of", "json", str(clip_path)],
            capture_output=True, text=True, timeout=60,
        )
        if clip_probe.returncode:
            raise RuntimeError(f"Clipe I2V da cena {index} não passou no FFprobe.")
        clip_meta = json.loads(clip_probe.stdout)
        clip_stream = next(
            (item for item in clip_meta.get("streams", []) if item.get("codec_type") == "video"),
            None,
        )
        clip_duration = float(clip_meta.get("format", {}).get("duration") or 0)
        if not clip_stream or clip_duration <= 0 or clip_path.stat().st_size < 10_000:
            raise RuntimeError(f"Clipe I2V da cena {index} está vazio ou sem vídeo válido.")
        if clip_stream.get("width") != 512 or clip_stream.get("height") != 896:
            raise RuntimeError(
                f"Clipe I2V da cena {index} tem resolução inesperada "
                f"{clip_stream.get('width')}x{clip_stream.get('height')}."
            )
        animated_media.append({"path": str(clip_path)})

    media = animated_media
    output = work / "nexus_video.mp4"
    render_video_remotion(
        media,
        audio_path,
        output,
        plan,
        project_dir=root / "remotion",
        job_id=job_id,
    )

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=codec_name,codec_type,width,height",
         "-of", "json", str(output)],
        capture_output=True, text=True, timeout=90,
    )
    if probe.returncode:
        raise RuntimeError("FFprobe não conseguiu ler o MP4: " + probe.stderr[-2000:])
    metadata = json.loads(probe.stdout)
    streams = metadata.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    duration = float(metadata.get("format", {}).get("duration") or 0)
    if not video or video.get("width") != 720 or video.get("height") != 1280:
        raise RuntimeError("MP4 não contém vídeo vertical 720x1280.")
    if not audio:
        raise RuntimeError("MP4 final não contém áudio.")
    if abs(duration - expected_duration) > 0.75:
        raise RuntimeError(f"Duração final {duration:.2f}s diverge da meta {expected_duration:.2f}s.")
    if output.stat().st_size == 0:
        raise RuntimeError("MP4 final vazio.")

    summary = {
        "job_id": job_id,
        "output": str(output),
        "duration": duration,
        "requested_duration": requested_duration,
        "maximum_duration": maximum_duration,
        "narration_duration": narration_duration,
        "narration_provider": narration_provider,
        "width": video["width"],
        "height": video["height"],
        "audio_codec": audio.get("codec_name"),
        "video_codec": video.get("codec_name"),
        "images": generated,
        "motion_clips": [
            {key: value for key, value in clip.items() if key != "path"}
            for clip in motion_clips
        ],
        "visual_source": "Cloudflare FLUX.2 Klein + Modal LTX-Video I2V + Remotion",
        "total_i2v_seconds": round(
            sum(float(clip.get("duration_seconds") or 0) for clip in motion_clips), 3
        ),
        "total_i2v_inference_seconds": round(
            sum(float(clip.get("inference_seconds") or 0) for clip in motion_clips), 3
        ),
        "modal_call_wall_seconds": max(
            (float(clip.get("modal_call_wall_seconds") or 0) for clip in motion_clips), default=0
        ),
        "model_load_seconds": max(
            (float(clip.get("model_load_seconds") or 0) for clip in motion_clips), default=0
        ),
        "gpu_name": next((clip.get("gpu_name") for clip in motion_clips if clip.get("gpu_name")), None),
        "ltx_inference_steps": next((clip.get("num_inference_steps") for clip in motion_clips if clip.get("num_inference_steps")), None),
        "estimated_ltx_gpu_cost_usd": max(
            (float(clip.get("estimated_gpu_cost_usd") or 0) for clip in motion_clips), default=0
        ),
        "ltx_gpu_cost_budget_usd": next(
            (clip.get("gpu_cost_budget_usd") for clip in motion_clips if clip.get("gpu_cost_budget_usd")), None
        ),
    }
    report_path = work / "render-report.json"
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (work / "nexus_video.mp4.enc").write_bytes(encrypt_bytes(output.read_bytes(), encryption_secret))
    (work / "render-report.json.enc").write_text(
        encrypt_text(report_path.read_text(encoding="utf-8"), encryption_secret), encoding="ascii"
    )
    output.unlink(missing_ok=True)
    report_path.unlink(missing_ok=True)
    print(json.dumps({key: value for key, value in summary.items() if key != "images"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
