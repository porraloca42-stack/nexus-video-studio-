"""Build a full generated-image video on an isolated GitHub Actions worker."""
import json
import os
import subprocess
from pathlib import Path

from nexus.audio import make_voice
from nexus.cloudflare_images import generate_scene_images
from nexus.remotion_renderer import render_video_remotion
from nexus.render_crypto import decrypt_text, encrypt_bytes, encrypt_text


def main():
    raw = os.environ.get("NEXUS_MANIFEST_ENCRYPTED", "")
    encryption_secret = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not raw or not encryption_secret:
        raise RuntimeError("Manifesto criptografado ou segredo de criptografia ausente.")
    plan = json.loads(decrypt_text(raw, encryption_secret))
    scenes = plan.get("scenes") or []
    if not scenes:
        raise RuntimeError("O manifesto não contém cenas.")
    job_id = os.environ.get("NEXUS_JOB_ID", "nexus-job")
    voice = os.environ.get("NEXUS_VOICE", "pt-BR-AntonioNeural")
    root = Path(__file__).resolve().parents[1]
    work = root / "worker_output" / job_id
    work.mkdir(parents=True, exist_ok=True)

    generated = generate_scene_images(
        scenes,
        work / "images",
        steps=int(os.environ.get("CLOUDFLARE_IMAGE_STEPS", "6")),
    )
    media = [{"path": item["path"]} for item in generated]

    narration = " ".join(str(scene.get("voiceover", "")).strip() for scene in scenes).strip()
    if not narration:
        raise RuntimeError("Narração vazia.")
    audio_path, subtitles_path = make_voice(narration, voice, work / "narration.mp3")

    output = work / "nexus_video.mp4"
    render_video_remotion(
        media,
        audio_path,
        output,
        plan,
        subtitles_path=subtitles_path,
        project_dir=root / "remotion",
        job_id=job_id,
    )

    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration,size:stream=codec_name,codec_type,width,height",
            "-of", "json", str(output),
        ],
        capture_output=True,
        text=True,
        timeout=90,
    )
    if probe.returncode:
        raise RuntimeError("FFprobe não conseguiu ler o MP4: " + probe.stderr[-2000:])
    metadata = json.loads(probe.stdout)
    streams = metadata.get("streams", [])
    video = next((item for item in streams if item.get("codec_type") == "video"), None)
    audio = next((item for item in streams if item.get("codec_type") == "audio"), None)
    duration = float(metadata.get("format", {}).get("duration") or 0)
    expected = sum(float(scene.get("duration_seconds") or scene.get("duration") or 0) for scene in scenes)
    if not video or video.get("width") != 720 or video.get("height") != 1280:
        raise RuntimeError("MP4 não contém vídeo vertical 720x1280.")
    if not audio:
        raise RuntimeError("MP4 final não contém áudio.")
    if abs(duration - expected) > 0.75:
        raise RuntimeError(f"Duração final {duration:.2f}s diverge da meta {expected:.2f}s.")
    if output.stat().st_size == 0:
        raise RuntimeError("MP4 final vazio.")

    summary = {
        "job_id": job_id,
        "output": str(output),
        "duration": duration,
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
