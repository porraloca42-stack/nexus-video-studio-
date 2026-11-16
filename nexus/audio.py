import asyncio
from pathlib import Path
import textwrap

import edge_tts


def _srt_timestamp(milliseconds):
    milliseconds = max(0, int(milliseconds))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def _subtitle_cues(events, narration):
    """Build SRT cues directly from Edge TTS timing events (100 ns ticks)."""
    timed_words = []
    timed_sentences = []

    for event in events:
        try:
            start = int(event.get("offset", 0)) / 10_000
            duration = max(1, int(event.get("duration", 0)) / 10_000)
            content = str(event.get("text") or "").strip()
        except (TypeError, ValueError):
            continue
        if not content:
            continue
        item = (start, start + duration, content)
        if event.get("type") == "WordBoundary":
            timed_words.append(item)
        elif event.get("type") == "SentenceBoundary":
            timed_sentences.append(item)

    # Prefer sentence-level cues so captions read as natural phrases instead of
    # isolated word flashes. Fall back to grouped word boundaries only when the
    # voice provider does not emit sentence timing.
    timed = timed_sentences or timed_words
    if not timed:
        # Keep production resilient if a provider stops emitting timing events.
        # This fallback is approximate, but still produces a valid subtitle file.
        words = str(narration or "").split()
        if not words:
            return []
        total_ms = max(2_000, int(len(words) / 2.5 * 1_000))
        duration = total_ms / len(words)
        timed = [
            (index * duration, (index + 1) * duration, word)
            for index, word in enumerate(words)
        ]

    cues = []
    group = []
    group_start = None
    group_end = 0

    def flush():
        nonlocal group, group_start, group_end
        if not group:
            return
        words = group
        # Split short phrases evenly over at most two mobile-safe lines.
        split_at = (len(words) + 1) // 2
        lines = [
            " ".join(words[:split_at]).strip(),
            " ".join(words[split_at:]).strip(),
        ]
        caption = "\n".join(line for line in lines if line)
        cues.append((group_start, group_end, caption))
        group = []
        group_start = None
        group_end = 0

    for start, end, content in timed:
        for word in content.split():
            candidate = " ".join(group + [word])
            elapsed = (end - group_start) if group_start is not None else 0
            sentence_end = word.endswith((".", "!", "?", "…"))
            if group and (
                len(candidate) > 52
                or len(group) >= 7
                or elapsed >= 3_200
                or (sentence_end and len(candidate) >= 14 and not timed_sentences)
            ):
                flush()
            if group_start is None:
                group_start = start
            group.append(word)
            group_end = max(group_end, end)
    flush()

    # Ensure cues never overlap and stack on screen.
    normalized = []
    for index, (start, end, caption) in enumerate(cues):
        if index + 1 < len(cues):
            next_start = cues[index + 1][0]
            safe_end = min(int(end), int(next_start) - 40)
        else:
            safe_end = int(end)
        safe_end = max(int(start) + 250, safe_end)
        normalized.append((max(0, int(start)), safe_end, caption))
    return normalized


def _write_srt(cues, destination):
    blocks = []
    for index, (start, end, caption) in enumerate(cues, start=1):
        blocks.append(
            f"{index}\n"
            f"{_srt_timestamp(start)} --> {_srt_timestamp(end)}\n"
            f"{caption}"
        )
    Path(destination).write_text("\n\n".join(blocks) + ("\n" if blocks else ""), encoding="utf-8")


def _fish_timestamp_cues(events, narration):
    aligned = []
    for event in events:
        alignment = event.get("alignment") or {}
        for item in alignment.get("segments") or []:
            try:
                start = max(0, round(float(item.get("start", 0)) * 1000))
                end = max(start + 1, round(float(item.get("end", 0)) * 1000))
                word = str(item.get("text") or "").strip()
            except (TypeError, ValueError):
                continue
            if word:
                aligned.append((start, end, word))
    if not aligned:
        return _subtitle_cues([], narration)
    return _subtitle_cues(
        [{"type": "WordBoundary", "offset": start * 10_000,
          "duration": (end - start) * 10_000, "text": word}
         for start, end, word in aligned],
        narration,
    )


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
    events = []
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
        if event.get("alignment"):
            events.append(event)
    if not audio_parts:
        raise RuntimeError("Fish Audio não retornou segmentos de áudio.")
    output.write_bytes(b"".join(audio_parts))
    cues = _fish_timestamp_cues(events, text)
    _write_srt(cues, output.with_suffix(".srt"))
    return output, output.with_suffix(".srt")


def make_voice(text, voice, output, fish_api_key=None, fish_voice_id=None, session=None):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    subtitles = output.with_suffix(".srt")

    if fish_api_key:
        try:
            result = _make_fish_voice(
                text, output, fish_api_key, voice_id=fish_voice_id, session=session
            )
            if not output.exists() or output.stat().st_size == 0:
                raise RuntimeError("Fish Audio retornou um arquivo de áudio vazio.")
            return result
        except Exception:
            # Preserve a working production path while the external TTS provider
            # is unavailable, rate-limited, or outside its temporary free window.
            output.unlink(missing_ok=True)
            subtitles.unlink(missing_ok=True)

    async def generate():
        communicate = edge_tts.Communicate(text, voice, rate="+0%")
        boundary_events = []
        with output.open("wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk.get("type") == "audio":
                    audio_file.write(chunk["data"])
                elif chunk.get("type") in ("WordBoundary", "SentenceBoundary"):
                    boundary_events.append(chunk)

        cues = _subtitle_cues(boundary_events, text)
        _write_srt(cues, subtitles)

    asyncio.run(generate())
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("O sintetizador não gerou um arquivo de áudio válido.")
    if not subtitles.exists():
        raise RuntimeError("Não foi possível criar o arquivo de legendas SRT.")
    return output, subtitles
