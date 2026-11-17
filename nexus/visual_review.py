"""Multimodal editorial review for rendered NEXUS scenes.

The review is advisory: it never silently rewrites an approved storyboard or
blocks delivery when the review service is unavailable.
"""
import base64
import json
import subprocess
from pathlib import Path

import requests


def normalize_review(payload, scenes):
    """Validate model output and align every review item to its scene number."""
    if not isinstance(payload, dict):
        raise ValueError("A auditoria visual não retornou um objeto JSON.")
    raw = payload.get("reviews")
    if not isinstance(raw, list):
        raise ValueError("A auditoria visual não retornou a lista reviews.")
    by_number = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            number = int(item.get("scene_number"))
        except (TypeError, ValueError):
            continue
        if not 1 <= number <= len(scenes):
            continue
        score = item.get("semantic_score", 0)
        try:
            score = max(0, min(10, int(round(float(score)))))
        except (TypeError, ValueError):
            score = 0
        def bounded_score(value):
            try:
                return max(0, min(10, int(round(float(value)))))
            except (TypeError, ValueError):
                return 0

        by_number[number] = {
            "scene_number": number,
            "semantic_score": score,
            "matches_narration": bool(item.get("matches_narration", False)),
            "motion_progression_score": bounded_score(item.get("motion_progression_score")),
            "action_observed": bool(item.get("action_observed", False)),
            "continuity_score": bounded_score(item.get("continuity_score")),
            "temporal_progression": str(item.get("temporal_progression") or "")[:500],
            "visual_quality": str(item.get("visual_quality") or "")[:500],
            "issues": [str(x)[:180] for x in (item.get("issues") or [])[:5]],
            "critical_issues": [str(x)[:180] for x in (item.get("critical_issues") or [])[:5]],
            "recommendation": str(item.get("recommendation") or "")[:500],
        }
    result = []
    for number, scene in enumerate(scenes, 1):
        result.append(by_number.get(number, {
            "scene_number": number,
            "semantic_score": 0,
            "matches_narration": False,
            "visual_quality": "Cena não avaliada pelo modelo.",
            "issues": ["missing_review"],
            "recommendation": "Revisão manual necessária.",
        }))
    return result


def review_scene_frames(frame_paths, scenes, api_key, model=None, timeout=180, session=None):
    """Review one or three ordered frames per scene against narration and continuity."""
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY ausente para auditoria visual.")
    if not scenes or len(frame_paths) not in (len(scenes), len(scenes) * 3):
        raise ValueError("A auditoria exige um ou três quadros ordenados por cena.")
    frames_per_scene = len(frame_paths) // len(scenes)
    temporal = frames_per_scene == 3
    prompt = (
        "Você é revisor editorial audiovisual. Cada cena vem acompanhada de "
        + ("três quadros em ordem temporal: início, meio e fim. " if temporal else "um quadro representativo. ")
        + "Compare as imagens com a fala e a ação da cena. Avalie aderência semântica, qualidade, composição, artefatos, "
        "texto/logos indesejados e continuidade de estilo. "
        + ("Use a sequência para observar movimento real, progressão da ação e repetição; não confunda zoom digital "
           "ou mudanças pequenas de enquadramento com ação significativa. " if temporal else
           "Não infira movimento a partir de um quadro estático. ")
        + "Se as imagens não permitirem concluir algo, registre a limitação; nunca invente movimento que os quadros não mostram. "
        "Avalie separadamente semantic_score (0–10, aderência à fala), matches_narration (booleano), motion_progression_score "
        "(0–10, mudança física real entre início/meio/fim), action_observed (booleano, ação principal realmente executada), "
        "continuity_score (0–10, identidade, cenário, luz e estilo), temporal_progression (descreva o que efetivamente muda). "
        "Separe issues comuns de critical_issues: falhas graves como identidade trocada, ação ausente, congelamento evidente, "
        "deformação ou contradição com a fala. Não dê nota alta só por beleza estética. Se o gesto não for observável, reduza "
        "motion_progression_score. Retorne somente JSON com a chave reviews; "
        "cada item deve conter scene_number, semantic_score, matches_narration, motion_progression_score, action_observed, "
        "continuity_score, temporal_progression, visual_quality, issues, critical_issues e recommendation. "
        "issues como lista e recommendation. Inclua uma avaliação por cena na ordem recebida.\nCENAS:\n"
        + json.dumps([
            {"scene_number": i + 1, "voiceover": scene.get("voiceover", ""),
             "visual_action": scene.get("visual_action", ""),
             "style": scene.get("visual_style", ""), "frames": frames_per_scene}
            for i, scene in enumerate(scenes)
        ], ensure_ascii=False)
    )
    parts = [{"text": prompt}]
    for index, path in enumerate(frame_paths):
        if temporal and index % 3 == 0:
            parts.append({"text": f"Sequência temporal da cena {index // 3 + 1}: início, meio e fim."})
        image_bytes = Path(path).read_bytes()
        parts.append({"inlineData": {
            "mimeType": "image/jpeg",
            "data": base64.b64encode(image_bytes).decode("ascii"),
        }})
    client = session or requests
    if model is None:
        from nexus.director import discover_models
        models = discover_models(api_key, "auto")[:5]
    else:
        models = [model]
    last_error = None
    text = ""
    for candidate_model in models:
        try:
            response = client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{candidate_model}:generateContent",
                params={"key": api_key},
                json={
                    "contents": [{"role": "user", "parts": parts}],
                    "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json", "maxOutputTokens": 4096},
                },
                timeout=timeout,
            )
            response.raise_for_status()
            candidates = response.json().get("candidates") or []
            text = "\n".join(
                p.get("text", "") for p in candidates[0].get("content", {}).get("parts", [])
                if isinstance(p, dict) and p.get("text")
            ) if candidates else ""
            if text.strip():
                break
        except requests.RequestException as exc:
            last_error = exc
    if not text.strip() and last_error:
        raise RuntimeError("Gemini não conseguiu concluir a auditoria visual.") from last_error
    if not text.strip():
        raise RuntimeError("Gemini não retornou conteúdo para a auditoria visual.")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        position = text.find("{")
        if position < 0:
            raise RuntimeError("Gemini retornou JSON inválido na auditoria visual.")
        payload, _ = json.JSONDecoder().raw_decode(text[position:])
    return normalize_review(payload, scenes)

def extract_scene_frames(video_path, scenes, output_dir):
    """Extract three ordered JPEG frames per scene for temporal editorial review."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True, timeout=45,
    )
    if probe.returncode:
        raise RuntimeError("Não foi possível medir o MP4 para auditoria visual.")
    total = float(probe.stdout.strip())
    durations = [float(scene.get("duration_seconds") or scene.get("duration") or 0) for scene in scenes]
    if not scenes or any(value <= 0 for value in durations):
        raise ValueError("Durações de cena inválidas para auditoria visual.")
    if abs(sum(durations) - total) > 1.5:
        raise RuntimeError("A linha do tempo do storyboard diverge do MP4; auditoria cancelada.")
    paths = []
    cursor = 0.0
    for index, duration in enumerate(durations, 1):
        for frame_index, fraction in enumerate((0.2, 0.5, 0.8), 1):
            timestamp = min(total - 0.08, cursor + duration * fraction)
            frame = output_dir / f"scene_review_{index:02d}_{frame_index}.jpg"
            result = subprocess.run(
                ["ffmpeg", "-y", "-ss", f"{timestamp:.3f}", "-i", str(video_path),
                 "-frames:v", "1", "-vf", "scale=512:-2", "-q:v", "7", str(frame)],
                capture_output=True, text=True, timeout=45,
            )
            if result.returncode or not frame.is_file() or frame.stat().st_size < 500:
                raise RuntimeError(f"Não foi possível extrair o quadro {frame_index} da cena {index}.")
            paths.append(str(frame))
        cursor += duration
    return paths
