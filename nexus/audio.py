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

    # Word boundaries provide the best synchronization. Sentence boundaries
    # are a valid fallback for Edge TTS configurations that omit word events.
    timed = timed_words or timed_sentences
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
                len(candidate) > 34
                or len(group) >= 4
                or elapsed >= 1_900
                or (sentence_end and len(candidate) >= 14)
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


def make_voice(text, voice, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    subtitles = output.with_suffix(".srt")

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
        raise RuntimeError("O Edge TTS não gerou um arquivo de áudio válido.")
    if not subtitles.exists():
        raise RuntimeError("Não foi possível criar o arquivo de legendas SRT.")
    return output, subtitles
