"""Fish Audio voice discovery, previews and narration.

NEXUS intentionally has no robotic system-TTS fallback: a Fish Audio failure is
reported clearly instead of silently changing the selected voice.
"""
import base64
import json
from pathlib import Path
from urllib.parse import urljoin

import requests


FISH_API = "https://api.fish.audio"
FISH_TTS_MODEL = "s2.1-pro-free"
FISH_VOICE_TEXT = "Olá! Esta é uma amostra da minha voz para a narração do seu vídeo. Vamos transformar essa ideia em uma história que prende a atenção."


class FishAudioError(RuntimeError):
    """Raised when Fish Audio cannot list voices or synthesize speech."""


def _fish_headers(api_key, model=None):
    if not api_key:
        raise FishAudioError("Configure FISH_API_KEY nos Secrets do Streamlit.")
    headers = {"Authorization": f"Bearer {api_key}"}
    if model:
        headers["model"] = model
    return headers


def list_fish_voices(api_key, *, page=1, page_size=6, title="", language="pt", self_only=False, session=None):
    """List public Fish Audio TTS voices, including their published sample audio."""
    client = session or requests
    params = {
        "page_size": max(1, min(int(page_size), 100)),
        "page_number": max(1, int(page)),
        "sort_by": "task_count",
    }
    if title and title.strip():
        params["title"] = title.strip()
    if language:
        params["language"] = language
    if self_only:
        params["self"] = "true"
    response = client.get(
        f"{FISH_API}/model",
        headers=_fish_headers(api_key),
        params=params,
        timeout=30,
    )
    try:
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        detail = getattr(response, "text", "")[:500]
        raise FishAudioError(f"Não foi possível consultar a biblioteca Fish Audio: {detail or exc}") from exc

    data = payload.get("data")
    items = payload.get("items") or (data.get("items") if isinstance(data, dict) else []) or []
    voices = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("type") not in (None, "", "tts"):
            continue
        if item.get("state") not in (None, "", "trained"):
            continue
        if not self_only and item.get("visibility") not in (None, "", "public"):
            continue
        samples = item.get("samples") or []
        sample = next((entry for entry in samples if isinstance(entry, dict) and entry.get("audio")), {})
        sample_audio = sample.get("audio") or sample.get("audio_url") or item.get("preview_url") or ""
        if sample_audio and not sample_audio.startswith(("http://", "https://", "data:")):
            sample_audio = urljoin(f"{FISH_API}/", sample_audio.lstrip("/"))
        voices.append({
            "id": str(item.get("_id") or item.get("id") or ""),
            "title": str(item.get("title") or "Voz sem título"),
            "description": str(item.get("description") or ""),
            "languages": item.get("languages") or [],
            "tags": item.get("tags") or [],
            "author": (item.get("author") or {}).get("nickname", ""),
            "sample_audio": sample_audio,
            "sample_text": sample.get("text") or "",
            "visibility": item.get("visibility", "public"),
            "task_count": int(item.get("task_count") or 0),
        })
    total = payload.get("total")
    if total is None and isinstance(data, dict):
        total = data.get("total")
    return {"total": int(total or len(voices)), "items": voices}


def generate_fish_preview(api_key, voice_id, *, text=FISH_VOICE_TEXT, session=None):
    """Generate a short preview for a voice model that has no published sample."""
    if not voice_id:
        raise FishAudioError("Selecione uma voz Fish Audio antes de gerar a amostra.")
    client = session or requests
    response = client.post(
        f"{FISH_API}/v1/tts",
        headers={
            **_fish_headers(api_key, FISH_TTS_MODEL),
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "reference_id": voice_id,
            "format": "mp3",
            "normalize": True,
            "language": "pt-BR",
        },
        timeout=(20, 120),
    )
    try:
        response.raise_for_status()
    except Exception as exc:
        raise FishAudioError(f"Fish Audio não conseguiu gerar a amostra: {getattr(response, 'text', '')[:500]}") from exc
    content_type = response.headers.get("content-type", "").lower()
    if not response.content or "json" in content_type:
        raise FishAudioError("Fish Audio não retornou um arquivo de áudio MP3 válido para a amostra.")
    return response.content


def _make_fish_voice(text, output, api_key, voice_id, session=None):
    """Generate Fish S2.1 Pro Free audio and concatenate native timestamped SSE chunks."""
    client = session or requests
    payload = {
        "text": text,
        "reference_id": voice_id,
        "format": "mp3",
        "sample_rate": 44100,
        "mp3_bitrate": 128,
        "normalize": True,
        "language": "pt-BR",
        "temperature": 0.72,
        "top_p": 0.75,
        "chunk_length": 300,
        "condition_on_previous_chunks": True,
    }
    response = client.post(
        f"{FISH_API}/v1/tts/stream/with-timestamp",
        headers={
            **_fish_headers(api_key, FISH_TTS_MODEL),
            "Content-Type": "application/json",
        },
        json=payload,
        stream=True,
        timeout=(20, 240),
    )
    response.raise_for_status()
    audio_parts = []
    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            continue
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            event = json.loads(data)
        except json.JSONDecodeError:
            continue
        encoded = event.get("audio_base64")
        if encoded:
            audio_parts.append(base64.b64decode(encoded))
    if not audio_parts:
        raise FishAudioError("Fish Audio não retornou segmentos de áudio.")
    output.write_bytes(b"".join(audio_parts))
    return output


def make_voice(text, voice, output, fish_api_key=None, fish_voice_id=None, session=None, return_provider=False):
    """Generate narration only with the selected Fish voice; never fall back to Edge TTS."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    voice_id = fish_voice_id or voice
    if not fish_api_key:
        raise FishAudioError("Narração interrompida: FISH_API_KEY não está configurada. Nenhuma voz robótica será usada.")
    if not voice_id:
        raise FishAudioError("Selecione uma voz da biblioteca Fish Audio antes de produzir o vídeo.")
    try:
        result = _make_fish_voice(text, output, fish_api_key, voice_id=voice_id, session=session)
        if not output.exists() or output.stat().st_size == 0:
            raise FishAudioError("Fish Audio retornou um arquivo de áudio vazio.")
    except Exception as exc:
        output.unlink(missing_ok=True)
        if isinstance(exc, FishAudioError):
            raise
        raise FishAudioError(
            f"Fish Audio falhou ao gerar a voz selecionada ({str(exc)[:220]}). "
            "A produção foi interrompida para não substituir a voz por uma narração robótica."
        ) from exc
    return (result, "Fish Audio S2.1 Pro Free") if return_provider else result
