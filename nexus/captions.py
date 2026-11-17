"""Deterministic captions built only from provider-supplied narration alignment."""
from __future__ import annotations

import math
import re
from typing import Any


_SENTENCE_END = re.compile(r"[.!?…][\"'”’»)]*$")
_DEFAULT_MAX_WORDS = 5
_DEFAULT_MAX_CHARS = 34
_MAX_PHRASE_CHARS = 56


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def build_alignment_caption_events(
    segments: Any,
    audio_duration_seconds: float,
    *,
    max_words: int = _DEFAULT_MAX_WORDS,
    max_chars: int = _DEFAULT_MAX_CHARS,
    max_phrase_chars: int = _MAX_PHRASE_CHARS,
) -> dict[str, Any]:
    """Create readable cues without fabricating timing between phrase-level segments.

    Word-aligned segments are grouped into short cues while preserving every
    source word's exact interval for the Remotion karaoke highlight. If the
    provider returns phrase-level alignment, each phrase remains one plain cue.
    Overlong phrase cues are omitted and reported rather than assigned invented
    sub-word timings.
    """
    if not _is_number(audio_duration_seconds) or audio_duration_seconds <= 0:
        return {"events": [], "alignment_level": "unavailable", "warning": "Duração do áudio inválida."}
    if not isinstance(segments, list) or not segments:
        return {"events": [], "alignment_level": "unavailable", "warning": "A Fish Audio não forneceu timestamps de narração."}
    if max_words < 1 or max_chars < 1 or max_phrase_chars < 1:
        raise ValueError("Caption chunk limits must be positive.")

    normalized: list[dict[str, Any]] = []
    previous_start = -1.0
    previous_end = -1.0
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            return {"events": [], "alignment_level": "unavailable", "warning": f"Segmento de alinhamento {index + 1} inválido."}
        text = str(segment.get("text") or "").strip()
        start = segment.get("start_seconds")
        end = segment.get("end_seconds")
        if (
            not text
            or not _is_number(start)
            or not _is_number(end)
            or start < 0
            or end <= start
            or start < previous_start
            or start < previous_end - 0.05
            or end > float(audio_duration_seconds) + 0.05
        ):
            return {"events": [], "alignment_level": "unavailable", "warning": f"Os timestamps da narração são inválidos no segmento {index + 1}."}
        item = {
            "text": text,
            "start_seconds": float(start),
            "end_seconds": min(float(end), float(audio_duration_seconds)),
        }
        if not any(char.isalnum() for char in text) and normalized:
            # Punctuation-only provider segments belong to the preceding spoken token.
            normalized[-1]["text"] += text
            normalized[-1]["end_seconds"] = item["end_seconds"]
        else:
            normalized.append(item)
        previous_start = float(start)
        previous_end = float(end)

    if not normalized:
        return {"events": [], "alignment_level": "unavailable", "warning": "Os timestamps não contêm palavras narradas."}

    is_word_aligned = all(
        len(item["text"].split()) == 1 and any(char.isalnum() for char in item["text"])
        for item in normalized
    )
    events: list[dict[str, Any]] = []
    warnings: list[str] = []

    if is_word_aligned:
        group: list[dict[str, Any]] = []

        def flush() -> None:
            if not group:
                return
            words = [
                {
                    "text": item["text"],
                    "start_seconds": item["start_seconds"],
                    "end_seconds": item["end_seconds"],
                    "emphasis": False,
                }
                for item in group
            ]
            events.append({
                "id": f"caption-{len(events) + 1:03d}",
                "start_seconds": words[0]["start_seconds"],
                "end_seconds": words[-1]["end_seconds"],
                "text": " ".join(word["text"] for word in words),
                "position": "bottom",
                "words": words,
            })
            group.clear()

        for item in normalized:
            proposed = " ".join([word["text"] for word in group] + [item["text"]])
            gap = item["start_seconds"] - group[-1]["end_seconds"] if group else 0
            if group and (
                len(group) >= max_words
                or len(proposed) > max_chars
                or gap > 0.45
            ):
                flush()
            group.append(item)
            if _SENTENCE_END.search(item["text"]):
                flush()
        flush()
        return {"events": events, "alignment_level": "word", "warning": None}

    for item in normalized:
        if len(item["text"]) > max_phrase_chars:
            warnings.append(
                f"Um trecho alinhado por frase excedeu {max_phrase_chars} caracteres e foi omitido para evitar legenda ilegível."
            )
            continue
        events.append({
            "id": f"caption-{len(events) + 1:03d}",
            "start_seconds": item["start_seconds"],
            "end_seconds": item["end_seconds"],
            "text": item["text"],
            "position": "bottom",
            "words": [],
        })

    if warnings and not events:
        warning = " ".join(dict.fromkeys(warnings))
    elif warnings:
        warning = " ".join(dict.fromkeys(warnings))
    else:
        warning = "Alinhamento por frase: as legendas usam os intervalos exatos do provedor, sem destaque palavra a palavra."
    return {
        "events": events,
        "alignment_level": "phrase" if events else "unavailable",
        "warning": warning if warnings or events else "Nenhum segmento de legenda utilizável foi encontrado.",
    }


def captions_cover_word_alignment(events: Any, word_timestamps: Any) -> bool:
    """Return true only when the caption word sequence exactly covers aligned speech."""
    if not isinstance(events, list) or not events or not isinstance(word_timestamps, list) or not word_timestamps:
        return False

    def normalize(value: Any) -> str:
        return re.sub(r"[^\wÀ-ÖØ-öø-ÿ]+", "", str(value or "").casefold())

    expected = [normalize(item.get("text")) for item in word_timestamps if isinstance(item, dict)]
    actual = [
        normalize(word.get("text"))
        for event in events if isinstance(event, dict)
        for word in event.get("words", []) if isinstance(word, dict)
    ]
    return bool(expected) and actual == expected
