"""Fish Audio voice discovery, previews and narration.

NEXUS intentionally has no robotic system-TTS fallback: a Fish Audio failure is
reported clearly instead of silently changing the selected voice.
"""
import base64
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin

import requests


FISH_API = "https://api.fish.audio"
FISH_TTS_MODEL = "s2.1-pro-free"
FISH_VOICE_TEXT = "Olá! Esta é uma amostra da minha voz para a narração do seu vídeo. Vamos transformar essa ideia em uma história que prende a atenção."

# Fish Audio first-party Brazilian Portuguese profiles verified on the official
# voice pages. IDs are checked again at runtime against author, title, locale,
# public visibility, and a published sample before entering the app catalog.
FISH_OFFICIAL_PTBR_NARRATORS = {
    "b3c060cc41544a7da94a2c487647c902": {"title": "Letícia", "gender": "female"},
    "add7bcb8d3c8423bbfa152ca232aad6e": {"title": "Ricardo", "gender": "male"},
    "0ffee1af32254090b3630823baade12b": {"title": "Rafael (Brasil)", "gender": "male"},
    "0e26d2df0d0848e3b34099bfb55fd6ea": {"title": "Beatriz (Brasil)", "gender": "female"},
}


class FishAudioError(RuntimeError):
    """Raised when Fish Audio cannot list voices or synthesize speech."""


def _fish_headers(api_key, model=None):
    if not api_key:
        raise FishAudioError("Configure FISH_API_KEY nos Secrets do Streamlit.")
    headers = {"Authorization": f"Bearer {api_key}"}
    if model:
        headers["model"] = model
    return headers


def list_fish_voices(api_key, *, page=1, page_size=6, title="", tags=None, language="pt", self_only=False, licensed_only=False, sort_by="score", session=None):
    """List public Fish Audio TTS voices, including their published sample audio."""
    client = session or requests
    params = {
        "page_size": max(1, min(int(page_size), 100)),
        "page_number": max(1, int(page)),
        "sort_by": sort_by,
    }
    if title and title.strip():
        params["title"] = title.strip()
    for tag in (tags or []):
        params.setdefault("tag", []).append(tag)
    if language:
        params["language"] = language
    if self_only:
        params["self"] = "true"
    elif licensed_only:
        params["licensed"] = "true"
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
            "licensed": bool(item.get("licensed", False)),
            "source": str(item.get("source") or item.get("source_type") or item.get("model_source") or ""),
            "task_count": int(item.get("task_count") or 0),
        })
    total = payload.get("total")
    if total is None and isinstance(data, dict):
        total = data.get("total")
    return {"total": int(total or len(voices)), "items": voices}


def get_fish_voice(api_key, voice_id, *, session=None):
    """Fetch one explicitly curated public Fish voice by stable model ID."""
    if not voice_id:
        raise FishAudioError("ID da voz Fish Audio não informado.")
    client = session or requests
    response = client.get(
        f"{FISH_API}/model/{voice_id}",
        headers=_fish_headers(api_key),
        timeout=30,
    )
    try:
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        detail = getattr(response, "text", "")[:500]
        raise FishAudioError(f"Não foi possível carregar a voz Fish Audio: {detail or exc}") from exc
    item = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(item, dict):
        raise FishAudioError("A Fish Audio retornou dados inválidos para a voz selecionada.")
    if item.get("type") not in (None, "", "tts") or item.get("state") not in (None, "", "trained"):
        raise FishAudioError("A voz selecionada não está disponível para narração.")
    # Fish Audio uses "unlist" for models hidden from search but accessible by direct URL.
    # Allow public and unlisted models; private models remain blocked.
    if item.get("visibility") not in (None, "", "public", "unlist"):
        raise FishAudioError("A voz selecionada é privada e não está disponível.")
    samples = item.get("samples") or []
    sample = next((entry for entry in samples if isinstance(entry, dict) and entry.get("audio")), {})
    sample_audio = sample.get("audio") or sample.get("audio_url") or item.get("preview_url") or ""
    if sample_audio and not sample_audio.startswith(("http://", "https://", "data:")):
        sample_audio = urljoin(f"{FISH_API}/", sample_audio.lstrip("/"))
    return {
        "id": str(item.get("_id") or item.get("id") or voice_id),
        "title": str(item.get("title") or "Voz sem título"),
        "description": str(item.get("description") or ""),
        "languages": item.get("languages") or [],
        "tags": item.get("tags") or [],
        "author": (item.get("author") or {}).get("nickname", ""),
        "sample_audio": sample_audio,
        "sample_text": sample.get("text") or "",
        "visibility": item.get("visibility", "public"),
        "licensed": bool(item.get("licensed", False)),
        "source": str(item.get("source") or item.get("source_type") or item.get("model_source") or ""),
        "gender": item.get("gender") or item.get("voice_gender") or item.get("sex") or "",
        "task_count": int(item.get("task_count") or 0),
    }


def list_curated_voice_catalog(api_key, *, session=None, max_workers=8):
    """Enrich the owner's fixed voice list with Fish metadata without losing supplied IDs."""
    from .voice_catalog import curated_voice_entries, infer_voice_gender

    entries = curated_voice_entries()
    def load(entry):
        base = {
            **entry,
            "title": f"Voz {entry['id'][:8]}",
            "description": "",
            "languages": [],
            "tags": [],
            "author": "",
            "sample_audio": "",
            "licensed": False,
            "source": "",
            "gender": "unknown",
            "metadata_available": False,
            "metadata_error": "",
        }
        try:
            metadata = get_fish_voice(api_key, entry["id"], session=session)
            base.update(metadata)
            base["id"] = entry["id"]
            base["category"] = entry["category"]
            base["gender"] = infer_voice_gender(metadata)
            base["metadata_available"] = True
        except Exception as exc:
            # Keep the exact user-supplied ID selectable even if metadata is
            # hidden, temporarily unavailable, or inaccessible to this API key.
            base["metadata_error"] = str(exc)[:220]
        return base

    with ThreadPoolExecutor(max_workers=max(1, min(int(max_workers), 12))) as executor:
        voices = list(executor.map(load, entries))
    return {
        category: [voice for voice in voices if voice["category"] == category]
        for category in dict.fromkeys(entry["category"] for entry in entries)
    }


def _is_natural_brazilian_voice(voice):
    """Keep only human-style Brazilian Portuguese narration/conversation voices."""
    title = (voice.get("title") or "").casefold()
    description = (voice.get("description") or "").casefold()
    tags = " ".join(voice.get("tags") or []).casefold()
    metadata = " ".join((title, description, tags))
    languages = " ".join(voice.get("languages") or []).casefold()
    if not any(token in languages for token in ("pt", "portugu")):
        return False
    excluded = (
        "meme", "anime", "personagem", "character", "lula", "bolsonaro",
        "celebrity", "celebridade", "ator", "actress", "movie", "filme",
        "game", "gaming", "jogo", "cartoon", "parody", "paródia",
    )
    if any(token in metadata for token in excluded):
        return False
    brazilian = (
        "brazilian", "brasileir", "português do brasil", "portugues do brasil",
        "portuguese (brazil)", "pt-br", "brasil",
    )
    if not any(token in metadata for token in brazilian):
        return False
    natural = (
        "narration", "narrador", "narradora", "conversational", "conversacional",
        "documentary", "documentário", "documentario", "professional", "profissional",
        "neutral", "neutro", "natural", "calm", "calmo", "calma", "warm", "acolhedor",
        "soft", "suave", "deep", "grave", "storytelling", "contação", "contacao",
        "voice over", "locução", "locucao",
    )
    return any(token in metadata for token in natural)


def list_fish_natural_brazilian_voices(api_key, *, session=None):
    """Discover a curated set of natural Brazilian Portuguese public voices.

    Uses Fish Audio's documented tag/title filters and merges duplicate models.
    Character, meme and public-figure impersonation models are excluded.
    """
    client = session or requests
    discovered = {}
    # Tags are queried separately because the API does not document whether
    # repeated tag filters are OR or AND.
    for tag in ("narration", "conversational", "documentary", "professional", "neutral"):
        result = list_fish_voices(
            api_key, page=1, page_size=100, tags=[tag], language="pt",
            sort_by="score", session=client,
        )
        for voice in result["items"]:
            if voice.get("id"):
                discovered[voice["id"]] = voice
    # Fish Official's two standard voices whose published descriptions
    # explicitly identify a Brazilian Portuguese accent.
    for title in ("Letícia", "Ricardo"):
        result = list_fish_voices(
            api_key, page=1, page_size=10, title=title, language="pt",
            sort_by="score", session=client,
        )
        for voice in result["items"]:
            if voice.get("id"):
                discovered[voice["id"]] = voice
    voices = [voice for voice in discovered.values() if _is_natural_brazilian_voice(voice)]
    voices.sort(key=lambda voice: (voice.get("task_count", 0)), reverse=True)
    return {"total": len(voices), "items": voices}



def _is_human_narrator_voice(voice, gender):
    """Accept human narration voices; reject fictional, celebrity and meme voices."""
    title = (voice.get("title") or "").casefold()
    description = (voice.get("description") or "").casefold()
    tags = [str(tag).casefold() for tag in (voice.get("tags") or [])]
    metadata = " ".join([title, description, *tags])
    languages = " ".join(str(lang).casefold() for lang in (voice.get("languages") or []))
    if not any(token in languages for token in ("pt", "portugu")):
        return False
    brazilian_markers = (
        "brazilian", "brasileir", "pt-br", "portuguese (brazil)",
        "português do brasil", "portugues do brasil",
    )
    language_context = f"{metadata} {languages}"
    if not any(token in language_context for token in brazilian_markers):
        return False
    european_markers = ("pt-pt", "european portuguese", "português europeu", "portugues europeu")
    if any(token in language_context for token in european_markers):
        return False
    metadata_words = re.findall(r"[a-záéíóúãõç]+", metadata)
    excluded = (
        "meme", "anime", "personagem", "character", "celebrity", "celebridade",
        "ator", "actress", "movie", "filme", "game", "gaming", "jogo",
        "cartoon", "parody", "paródia", "fictional", "fiction", "impersonation",
        "impersona", "imitação", "imitacao", "politician", "president",
        "dictator", "publicfigure", "public figure", "public-figure", "famous",
    )
    if any(word == token or word.startswith(token) for word in metadata_words for token in excluded):
        return False
    excluded_identity_phrases = (
        "adolf", "hitler", "lula", "bolsonaro", "donald trump", "joe biden",
        "barack obama", "papai noel", "santa claus", "mickey mouse",
        "donald duck", "bob esponja", "spongebob", "shrek", "darth vader",
        "harry potter", "sao cipriano", "são cipriano",
    )
    if any(phrase in language_context for phrase in excluded_identity_phrases):
        return False
    gender_terms = {
        "male": ("male", "mascul", "homem", "man"),
        "female": ("female", "feminin", "mulher", "woman"),
    }[gender]
    if not any(word.startswith(term) for word in metadata_words for term in gender_terms):
        return False
    return "narration" in tags or any(
        term in metadata for term in (
            "narration", "narrador", "narradora", "voice over", "locução",
            "locucao", "documentary", "documentário", "documentario",
        )
    )


def _is_curated_fish_official_ptbr_voice(voice, voice_id):
    """Verify a fixed first-party voice profile against its live Fish metadata."""
    expected = FISH_OFFICIAL_PTBR_NARRATORS.get(voice_id)
    if not expected:
        return False
    if voice.get("author", "").strip().casefold() != "fish official":
        return False
    if voice.get("title", "").strip().casefold() != expected["title"].casefold():
        return False
    if str(voice.get("visibility") or "public").casefold() != "public":
        return False
    if not voice.get("sample_audio"):
        return False
    languages = [str(language).casefold() for language in voice.get("languages", [])]
    if not any(language == "pt" or "portugu" in language for language in languages):
        return False
    metadata_probe = {
        **voice,
        # The pinned official profile IDs are documented by Fish as Brazilian
        # Portuguese and male/female. Add that verified profile metadata for the
        # common exclusion filter; the live ID/title/author checks above detect
        # a provider-side profile change.
        "description": f"{voice.get('description', '')} Brazilian Portuguese narration",
        "languages": [*languages, "pt-BR"],
        "tags": [*voice.get("tags", []), expected["gender"], "narration"],
    }
    if not _is_human_narrator_voice(metadata_probe, expected["gender"]):
        return False
    return True


def list_fish_professional_narrators(api_key, *, per_gender=25, session=None, require_sample=True):
    """Return licensed/PVC narrators plus a small, pinned Fish Official pt-BR set.

    Community voices must pass explicit metadata and source filters. First-party
    voices are individually pinned by stable model ID and revalidated against
    Fish's live title, author, language, visibility and sample fields.
    """
    client = session or requests
    result = {}
    for gender in ("male", "female"):
        discovered = {}
        for licensed_only in (False, True):
            for page_number in range(1, 6):
                page = list_fish_voices(
                    api_key, page=page_number, page_size=100,
                    tags=[gender], language="pt",
                    licensed_only=licensed_only, sort_by="task_count",
                    session=client,
                )
                for voice in page["items"]:
                    if not voice.get("id"):
                        continue
                    source = (voice.get("source") or "").casefold()
                    if not voice.get("licensed") and "pvc" not in source:
                        continue
                    if require_sample and not voice.get("sample_audio"):
                        continue
                    if _is_human_narrator_voice(voice, gender):
                        discovered[voice["id"]] = voice
                if not page["items"] or page_number * 100 >= page["total"]:
                    break
                if len(discovered) >= 25:
                    break

        for voice_id, profile in FISH_OFFICIAL_PTBR_NARRATORS.items():
            if profile["gender"] != gender or voice_id in discovered:
                continue
            try:
                voice = get_fish_voice(api_key, voice_id, session=client)
            except FishAudioError:
                continue
            if require_sample and not voice.get("sample_audio"):
                continue
            if _is_curated_fish_official_ptbr_voice(voice, voice_id):
                voice["official_verified"] = True
                voice["commercial_use_requires_paid_plan"] = True
                discovered[voice_id] = voice

        voices = sorted(
            discovered.values(),
            key=lambda voice: (
                bool(voice.get("licensed")),
                int(voice.get("task_count") or 0),
            ),
            reverse=True,
        )
        result[gender] = voices[:max(1, min(int(per_gender), 25))]
    return result

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


def _flatten_fish_alignment(alignment_by_chunk):
    """Convert Fish's latest per-chunk snapshots into global-time segments.

    Fish sends cumulative snapshots, so the last non-null snapshot for each
    chunk_seq replaces earlier snapshots. Segment times are local to that text
    chunk and must be shifted by chunk_audio_offset_sec.
    """
    segments = []
    for chunk_seq, snapshot in sorted(alignment_by_chunk.items()):
        offset = snapshot.get("offset")
        alignment = snapshot.get("alignment")
        if not isinstance(offset, (int, float)) or not isinstance(alignment, dict):
            continue
        for item in alignment.get("segments", []):
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            start, end = item.get("start"), item.get("end")
            if (
                not isinstance(text, str) or not text.strip()
                or not isinstance(start, (int, float))
                or not isinstance(end, (int, float))
                or end <= start
            ):
                continue
            segments.append({
                "text": text,
                "start_seconds": round(float(offset) + float(start), 6),
                "end_seconds": round(float(offset) + float(end), 6),
                "chunk_seq": chunk_seq,
            })
    return sorted(segments, key=lambda item: (item["start_seconds"], item["end_seconds"]))


def _make_fish_voice(text, output, api_key, voice_id, session=None, return_alignment=False):
    """Generate Fish audio and optionally preserve its timestamp alignment snapshots."""
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
    alignment_by_chunk = {}
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
        alignment = event.get("alignment")
        chunk_seq = event.get("chunk_seq")
        offset = event.get("chunk_audio_offset_sec")
        if (
            isinstance(alignment, dict)
            and isinstance(chunk_seq, int) and not isinstance(chunk_seq, bool)
            and isinstance(offset, (int, float))
        ):
            alignment_by_chunk[chunk_seq] = {
                "offset": float(offset),
                "alignment": alignment,
            }
    if not audio_parts:
        raise FishAudioError("Fish Audio não retornou segmentos de áudio.")
    output.write_bytes(b"".join(audio_parts))
    if return_alignment:
        return output, _flatten_fish_alignment(alignment_by_chunk)
    return output


def make_voice(text, voice, output, fish_api_key=None, fish_voice_id=None, session=None, return_provider=False, return_alignment=False):
    """Generate narration only with the selected Fish voice; never fall back to Edge TTS."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    voice_id = fish_voice_id or voice
    if not fish_api_key:
        raise FishAudioError("Narração interrompida: FISH_API_KEY não está configurada. Nenhuma voz robótica será usada.")
    if not voice_id:
        raise FishAudioError("Selecione uma voz da biblioteca Fish Audio antes de produzir o vídeo.")
    try:
        generated = _make_fish_voice(
            text, output, fish_api_key, voice_id=voice_id, session=session,
            return_alignment=return_alignment,
        )
        if return_alignment:
            result, alignment_segments = generated
        else:
            result, alignment_segments = generated, []
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
    if return_provider and return_alignment:
        return result, "Fish Audio S2.1 Pro Free", alignment_segments
    if return_provider:
        return result, "Fish Audio S2.1 Pro Free"
    if return_alignment:
        return result, alignment_segments
    return result
