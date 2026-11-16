"""Multimodal editorial review for rendered NEXUS scenes.

The review is advisory: it never silently rewrites an approved storyboard or
blocks delivery when the review service is unavailable.
"""
import base64
import json
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
        by_number[number] = {
            "scene_number": number,
            "semantic_score": score,
            "matches_narration": bool(item.get("matches_narration", False)),
            "visual_quality": str(item.get("visual_quality") or "")[:500],
            "issues": [str(x)[:180] for x in (item.get("issues") or [])[:5]],
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


def review_scene_frames(frame_paths, scenes, api_key, model="gemini-2.5-flash", timeout=180, session=None):
    """Review one representative rendered frame per scene against its narration."""
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY ausente para auditoria visual.")
    if len(frame_paths) != len(scenes) or not scenes:
        raise ValueError("A auditoria exige exatamente um quadro por cena.")
    parts = [{
        "text": (
            "Você é revisor editorial audiovisual. Compare cada quadro com a fala da cena "
            "correspondente. Avalie correspondência literal/semântica, qualidade visual, "
            "composição, artefatos, texto/logos indesejados e continuidade de estilo. "
            "Não infira movimento a partir de um quadro estático. Seja rigoroso e específico. "
            "Retorne somente JSON: {\\"reviews\\":[{\\"scene_number\\":1,"
            "\\"semantic_score\\":0-10,\\"matches_narration\\":true,"
            "\\"visual_quality\\":\\"...\\",\\"issues\\":[\\"...\\"],"
            "\\"recommendation\\":\\"...\\"}]}. "
            "Inclua exatamente uma avaliação para cada cena, na ordem recebida.\nCENAS:\n"
            + json.dumps([
                {"scene_number": i + 1, "voiceover": scene.get("voiceover", ""),
                 "visual_action": scene.get("visual_action", ""),
                 "style": scene.get("visual_style", "")}
                for i, scene in enumerate(scenes)
            ], ensure_ascii=False)
        )
    }]
    for path in frame_paths:
        image_bytes = Path(path).read_bytes()
        parts.append({"inline_data": {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_bytes).decode("ascii"),
        }})
    client = session or requests
    response = client.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": api_key},
        json={
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json", "maxOutputTokens": 4096},
        },
        timeout=timeout,
    )
    response.raise_for_status()
    candidates = response.json().get("candidates") or []
    text = "\\n".join(
        p.get("text", "") for p in candidates[0].get("content", {}).get("parts", [])
        if isinstance(p, dict) and p.get("text")
    ) if candidates else ""
    if not text.strip():
        raise RuntimeError("Gemini não retornou conteúdo para a auditoria visual.")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        if start < 0:
            raise RuntimeError("Gemini retornou JSON inválido na auditoria visual.")
        payload, _ = json.JSONDecoder().raw_decode(text[start:])
    return normalize_review(payload, scenes)
