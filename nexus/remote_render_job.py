"""Build a Cloudflare-image/Remotion video on an isolated GitHub Actions worker."""
import json
import os
import subprocess
from pathlib import Path

from nexus.audio import make_voice
from nexus.cloudflare_images import generate_scene_images
from nexus.remotion_renderer import render_video_remotion
from nexus.render_crypto import decrypt_text, encrypt_bytes, encrypt_text


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


def _fit_narration_to_timeline(audio_path: Path, target: float) -> float:
    """Gently time-stretch narration audio to the Remotion timeline; no captions are produced."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True, timeout=60,
    )
    if probe.returncode:
        raise RuntimeError("Não foi possível medir a duração da narração no worker.")
    actual = float(probe.stdout.strip())
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
    plan = json.loads(decrypt_text(raw, encryption_secret))
    fish_credentials = {"api_key": "", "voice_id": ""}
    if encrypted_fish:
        fish_credentials.update(json.loads(decrypt_text(encrypted_fish, encryption_secret)))
    scenes = plan.get("scenes") or []
    if not scenes:
        raise RuntimeError("O manifesto não contém cenas.")
    job_id = os.environ.get("NEXUS_JOB_ID", "nexus-job")
    voice = os.environ.get("NEXUS_VOICE", "pt-BR-AntonioNeural")
    root = Path(project_root or Path(__file__).resolve().parents[1])
    work = root / "worker_output" / job_id
    work.mkdir(parents=True, exist_ok=True)

    generated = generate_scene_images(
        scenes,
        work / "images",
        steps=int(os.environ.get("CLOUDFLARE_IMAGE_STEPS", "4")),
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

    narration = " ".join(str(scene.get("voiceover", "")).strip() for scene in scenes).strip()
    if not narration:
        raise RuntimeError("Narração vazia.")
    audio_path, narration_provider = generate_worker_narration(
        narration,
        voice,
        work / "narration.mp3",
        fish_api_key=fish_credentials.get("api_key", ""),
        fish_voice_id=fish_credentials.get("voice_id", ""),
    )
    expected_duration = sum(
        float(scene.get("duration_seconds") or scene.get("duration") or 0)
        for scene in scenes
    )
    narration_duration = _fit_narration_to_timeline(Path(audio_path), expected_duration)

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
        "narration_duration": narration_duration,
        "narration_provider": narration_provider,
        "width": video["width"],
        "height": video["height"],
        "audio_codec": audio.get("codec_name"),
        "video_codec": video.get("codec_name"),
        "images": generated,
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
