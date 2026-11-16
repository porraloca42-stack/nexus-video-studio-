"""Isolated adapter from the Python storyboard to the Remotion renderer.

The Streamlit app does not use this adapter by default. The Remotion runtime
must be installed separately on the render worker.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path


_TIMESTAMP = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+"
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})"
)


def _timestamp_frames(groups, fps):
    hours, minutes, seconds, millis = (int(value) for value in groups)
    total_seconds = hours * 3600 + minutes * 60 + seconds + millis / 1000
    return max(0, round(total_seconds * fps))


def parse_srt_captions(path, fps=30):
    """Convert SRT cues to frame-based caption segments."""
    if not path or not Path(path).is_file():
        return []
    content = Path(path).read_text(encoding="utf-8-sig")
    captions = []
    for block in re.split(r"\n\s*\n", content.strip()):
        lines = block.splitlines()
        match = next((_TIMESTAMP.search(line) for line in lines if _TIMESTAMP.search(line)), None)
        if not match:
            continue
        text_lines = lines[lines.index(match.string) + 1:] if match.string in lines else []
        text = " ".join(line.strip() for line in text_lines if line.strip())
        if not text:
            continue
        start = _timestamp_frames(match.groups()[:4], fps)
        end = _timestamp_frames(match.groups()[4:], fps)
        if end > start:
            captions.append({"text": text, "startFrame": start, "endFrame": end})
    return captions


def build_remotion_manifest(plan, media, audio_path, subtitles_path, public_dir, job_id="nexus-job"):
    """Copy approved assets into Remotion public/ and create a render manifest."""
    public_dir = Path(public_dir)
    job_dir = public_dir / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    scenes = []
    source_scenes = plan.get("scenes") or []
    for index, scene in enumerate(source_scenes):
        duration = float(scene.get("duration_seconds") or scene.get("duration") or 0)
        if duration <= 0:
            raise ValueError(f"Duração inválida na cena {index + 1}.")
        item = media[index] if index < len(media) else {}
        asset = item.get("path")
        asset_ref = None
        visual_mode = "graphic"
        if asset:
            source = Path(asset)
            if not source.is_file():
                raise FileNotFoundError(f"Arquivo de mídia da cena {index + 1} não encontrado: {source}")
            suffix = source.suffix.lower() or ".mp4"
            destination = job_dir / f"scene_{index + 1:02d}{suffix}"
            shutil.copy2(source, destination)
            asset_ref = f"jobs/{job_id}/{destination.name}"
            visual_mode = "video" if suffix in {".mp4", ".mov", ".webm", ".m4v"} else "image"
        scenes.append({
            "id": str(scene.get("id") or f"scene-{index + 1:02d}"),
            "durationSeconds": duration,
            "narration": str(scene.get("voiceover") or ""),
            "visualMode": visual_mode,
            "asset": asset_ref,
            # Descriptive copy and image prompts are director metadata, never
            # on-screen typography. Only narration captions are rendered.
            "imagePrompt": str(scene.get("image_prompt") or ""),
            "cameraMotion": str(scene.get("camera_motion") or "push_in"),
            "motionEvents": list(scene.get("motion_events") or []),
            "accent": str(scene.get("accent") or "#e8b66b"),
        })

    total_seconds = sum(scene["durationSeconds"] for scene in scenes)
    if not scenes or total_seconds <= 0:
        raise ValueError("O storyboard não contém cenas válidas.")

    fps = 30
    def copy_audio(path, name):
        if not path or not Path(path).is_file():
            return None
        source = Path(path)
        suffix = source.suffix.lower() or ".mp3"
        destination = job_dir / (Path(name).stem + suffix)
        shutil.copy2(source, destination)
        return f"jobs/{job_id}/{destination.name}"

    narration_ref = copy_audio(audio_path, "narration.mp3")
    captions = parse_srt_captions(subtitles_path, fps=fps)
    manifest = {
        "width": 720,
        "height": 1280,
        "fps": fps,
        "durationInFrames": round(total_seconds * fps),
        "title": str(plan.get("seo", {}).get("title") or plan.get("topic_interpretation") or "NEXUS VIDEO"),
        "narrationAudio": narration_ref,
        "scenes": scenes,
        "captions": captions,
    }
    manifest_path = job_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path, manifest


def render_video_remotion(media, audio_path, output, plan, subtitles_path=None, project_dir=None, job_id="nexus-job"):
    """Render a storyboard through an installed Remotion project."""
    project_dir = Path(project_dir or Path(__file__).resolve().parents[1] / "remotion")
    package_json = project_dir / "package.json"
    node_modules = project_dir / "node_modules"
    if not package_json.is_file() or not node_modules.is_dir():
        raise RuntimeError(
            "O motor Remotion está no repositório, mas o ambiente de renderização "
            "não possui as dependências Node instaladas."
        )
    manifest_path, _ = build_remotion_manifest(
        plan, media, audio_path, subtitles_path, project_dir / "public", job_id=job_id
    )
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "npx", "remotion", "render", "src/index.ts", "NexusFromManifest",
        str(output.resolve()), f"--props={manifest_path.relative_to(project_dir).as_posix()}",
        "--codec=h264", "--pixel-format=yuv420p",
    ]
    result = subprocess.run(command, cwd=project_dir, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout)[-5000:])
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("Remotion terminou sem produzir um MP4 válido.")
    return output
