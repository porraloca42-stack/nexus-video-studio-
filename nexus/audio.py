import asyncio
from pathlib import Path

import edge_tts


def _make_fish_voice(text, output, api_key, voice_id=None, session=None):
    """Generate Fish S2.1 Pro Free audio and native word alignment via SSE."""
    import base64
    import json
    import requests

    client = session or requests
    payload = {
        "text": text,
        "format": "mp3",
        "sample_rate": 44100,
        "mp3_bitrate": 128,
        "normalize": True,
        "language": "pt",
        "temperature": 0.72,
        "top_p": 0.75,
        "chunk_length": 300,
        "condition_on_previous_chunks": True,
    }
    if voice_id:
        payload["reference_id"] = voice_id
    response = client.post(
        "https://api.fish.audio/v1/tts/stream/with-timestamp",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "model": "s2.1-pro-free",
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
        raise RuntimeError("Fish Audio não retornou segmentos de áudio.")
    output.write_bytes(b"".join(audio_parts))
    return output


def make_voice(text, voice, output, fish_api_key=None, fish_voice_id=None, session=None, return_provider=False):
    """Generate narration audio only; captions are intentionally handled in post-production."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if fish_api_key:
        try:
            result = _make_fish_voice(
                text, output, fish_api_key, voice_id=fish_voice_id, session=session
            )
            if not output.exists() or output.stat().st_size == 0:
                raise RuntimeError("Fish Audio retornou um arquivo de áudio vazio.")
            return (result, "Fish Audio") if return_provider else result
        except Exception as exc:
            fish_error = str(exc)[:240]
            output.unlink(missing_ok=True)

    async def generate():
        communicate = edge_tts.Communicate(text, voice, rate="+0%")
        with output.open("wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk.get("type") == "audio":
                    audio_file.write(chunk["data"])

    asyncio.run(generate())
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("O sintetizador não gerou um arquivo de áudio válido.")
    provider = "Edge TTS" + (f" (fallback: {fish_error})" if fish_api_key else "")
    return (output, provider) if return_provider else output
