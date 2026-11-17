"""Isolated adapter from the Python storyboard to the Remotion renderer.

The Streamlit app does not use this adapter by default. The Remotion runtime
must be installed separately on the render worker.
"""
import json
import shutil
import subprocess
from pathlib import Path


_CAMERA_MOVES = {"push_in", "pull_out", "pan_left", "pan_right", "tilt_up", "tilt_down", "static"}
_LIGHT_CHANGES = {"none", "subtle_flicker", "light_sweep", "exposure_ramp"}
_ATMOSPHERE_EFFECTS = {"none", "dust", "rain", "fog", "embers", "particles"}
_TRANSITIONS = {"cut", "crossfade", "match_cut", "fade"}


def _bounded_number(value, default, minimum, maximum):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))


def sanitize_scene_direction(direction, fallback_camera="push_in"):
    """Whitelist and clamp Gemini's visual plan before it reaches Remotion."""
    if not isinstance(direction, dict):
        direction = {}
    camera = direction.get("camera") if isinstance(direction.get("camera"), dict) else {}
    depth = direction.get("depth_layers") if isinstance(direction.get("depth_layers"), dict) else {}
    lighting = direction.get("lighting") if isinstance(direction.get("lighting"), dict) else {}
    atmosphere = direction.get("atmosphere") if isinstance(direction.get("atmosphere"), dict) else {}
    transition = direction.get("transition") if isinstance(direction.get("transition"), dict) else {}
    move = str(camera.get("move") or fallback_camera)
    if move not in _CAMERA_MOVES:
        move = fallback_camera if fallback_camera in _CAMERA_MOVES else "push_in"
    focus = str(camera.get("focus") or "subject")
    if focus not in {"subject", "foreground", "background"}:
        focus = "subject"
    light_change = str(lighting.get("change") or "none")
    if light_change not in _LIGHT_CHANGES:
        light_change = "none"
    effect = str(atmosphere.get("effect") or "none")
    if effect not in _ATMOSPHERE_EFFECTS:
        effect = "none"
    transition_in = str(transition.get("in") or "cut")
    transition_out = str(transition.get("out") or "cut")
    if transition_in not in _TRANSITIONS:
        transition_in = "cut"
    if transition_out not in _TRANSITIONS:
        transition_out = "cut"
    raw_beats = direction.get("beats") if isinstance(direction.get("beats"), list) else []
    beats = []
    for beat in raw_beats[:3]:
        if not isinstance(beat, dict):
            continue
        beats.append({
            "at": _bounded_number(beat.get("at"), 0.5, 0.0, 1.0),
            "event": str(beat.get("event") or "")[:180],
            "visualTarget": str(beat.get("visual_target") or "")[:120],
        })
    return {
        "camera": {
            "move": move,
            "intensity": _bounded_number(camera.get("intensity"), 0.65, 0.0, 1.0),
            "startScale": _bounded_number(camera.get("start_scale"), 1.04, 1.02, 1.28),
            "endScale": _bounded_number(camera.get("end_scale"), 1.22, 1.02, 1.28),
            "focus": focus,
        },
        "depthLayers": {
            "foreground": str(depth.get("foreground") or "")[:180],
            "subject": str(depth.get("subject") or "")[:180],
            "background": str(depth.get("background") or "")[:180],
            "parallaxStrength": _bounded_number(depth.get("parallax_strength"), 0.0, 0.0, 1.0),
        },
        "lighting": {"mood": str(lighting.get("mood") or "")[:100], "keyDirection": str(lighting.get("key_direction") or "")[:100], "change": light_change},
        "atmosphere": {"effect": effect, "intensity": _bounded_number(atmosphere.get("intensity"), 0.0, 0.0, 1.0)},
        "transition": {"in": transition_in, "out": transition_out, "durationFrames": int(_bounded_number(transition.get("duration_frames"), 8, 0, 12))},
        "beats": beats,
    }


def build_remotion_manifest(plan, media, audio_path, public_dir, job_id="nexus-job"):
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
            # Descriptive copy and image prompts remain metadata, never on-screen text.
            "imagePrompt": str(scene.get("image_prompt") or ""),
            "cameraMotion": str(scene.get("camera_motion") or "push_in"),
            "motionEvents": list(scene.get("motion_events") or []),
            "sceneDirection": sanitize_scene_direction(scene.get("scene_direction"), scene.get("camera_motion") or "push_in"),
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
    music_ref = copy_audio(plan.get("music_audio_path"), "music.mp3")
    timeline = plan.get("edit_timeline") if isinstance(plan.get("edit_timeline"), dict) else {}

    caption_events = []
    for index, event in enumerate(timeline.get("caption_events") or [], 1):
        if not isinstance(event, dict):
            raise ValueError(f"Evento de legenda {index} inválido.")
        start = float(event.get("start_seconds") or 0)
        end = float(event.get("end_seconds") or 0)
        text = str(event.get("text") or "").strip()
        if not text or start < 0 or end <= start or end > total_seconds + 0.05:
            raise ValueError(f"Evento de legenda {index} tem texto ou intervalo inválido.")
        words = []
        for word in event.get("words") or []:
            if not isinstance(word, dict):
                raise ValueError(f"Palavra temporizada inválida na legenda {index}.")
            word_start = float(word.get("start_seconds") or 0)
            word_end = float(word.get("end_seconds") or 0)
            word_text = str(word.get("text") or "").strip()
            if not word_text or word_start < start - 0.05 or word_end <= word_start or word_end > end + 0.05:
                raise ValueError(f"Palavra temporizada fora do intervalo da legenda {index}.")
            words.append({
                "text": word_text,
                "startSeconds": word_start,
                "endSeconds": word_end,
                "emphasis": bool(word.get("emphasis", False)),
            })
        caption_events.append({
            "id": str(event.get("id") or f"caption-{index}"),
            "startSeconds": start,
            "endSeconds": end,
            "text": text,
            "position": event.get("position") if event.get("position") in {"top", "center", "bottom"} else "bottom",
            "words": words,
        })

    sfx_events = []
    for index, event in enumerate(timeline.get("sfx_events") or [], 1):
        if not isinstance(event, dict):
            raise ValueError(f"Evento SFX {index} inválido.")
        start = float(event.get("start_seconds") or 0)
        duration = float(event.get("duration_seconds") or 0)
        source_path = event.get("asset_path")
        if start < 0 or duration <= 0 or start + duration > total_seconds + 0.05:
            raise ValueError(f"Evento SFX {index} tem intervalo inválido.")
        asset_ref = copy_audio(source_path, f"sfx_{index:02d}.wav")
        if not asset_ref:
            raise FileNotFoundError(f"Arquivo SFX da timeline {index} não encontrado.")
        sfx_events.append({
            "id": str(event.get("id") or f"sfx-{index}"),
            "asset": asset_ref,
            "startSeconds": start,
            "durationSeconds": duration,
            "volume": _bounded_number(event.get("volume"), 0.25, 0.0, 1.0),
        })

    audio_mix_events = []
    for index, event in enumerate(timeline.get("audio_mix_events") or [], 1):
        if not isinstance(event, dict):
            raise ValueError(f"Evento de mixagem {index} inválido.")
        start = float(event.get("start_seconds") or 0)
        end = float(event.get("end_seconds") or 0)
        if start < 0 or end <= start or end > total_seconds + 0.05:
            raise ValueError(f"Evento de mixagem {index} tem intervalo inválido.")
        audio_mix_events.append({
            "startSeconds": start,
            "endSeconds": end,
            "musicVolume": _bounded_number(event.get("music_volume"), 0.06, 0.0, 1.0),
        })

    manifest = {
        "width": 720,
        "height": 1280,
        "fps": fps,
        "durationInFrames": round(total_seconds * fps),
        "title": str(plan.get("seo", {}).get("title") or plan.get("topic_interpretation") or "NEXUS VIDEO"),
        "narrationAudio": narration_ref,
        "musicAudio": music_ref,
        "musicVolume": _bounded_number(plan.get("music_volume"), 0.12, 0.0, 1.0),
        "captionEvents": caption_events,
        "soundEffects": sfx_events,
        "audioMixEvents": audio_mix_events,
        "scenes": scenes,
    }
    manifest_path = job_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path, manifest


def render_video_remotion(media, audio_path, output, plan, project_dir=None, job_id="nexus-job"):
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
        plan, media, audio_path, project_dir / "public", job_id=job_id
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
