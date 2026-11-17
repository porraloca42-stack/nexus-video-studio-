import base64, json, os, shutil, subprocess, tempfile, inspect, importlib, time
from pathlib import Path
import requests
import streamlit as st
import streamlit.components.v1 as components
from nexus.director import create_storyboard, validate_storyboard
from nexus.build_info import get_runtime_build_info
from nexus.assets import search_video_sources, download_file, diverse_candidate_shortlist
from nexus.render_modes import ECONOMY_MODE, RENDER_MODE_OPTIONS, default_render_mode, mode_uses_modal
import nexus.audio as fish_audio

# Streamlit Cloud can retain a stale imported module across source syncs.
# Reload the checked-out module before accessing helpers added in later commits.
fish_audio = importlib.reload(fish_audio)
if not hasattr(fish_audio, "get_fish_voice"):
    raise RuntimeError(
        "Módulo de áudio desatualizado no ambiente. "
        f"Arquivo carregado: {getattr(fish_audio, '__file__', 'desconhecido')}"
    )
from nexus.render import render_video


def _extract_visual_review_frames(video_path, output_dir, prefix):
    """Extract representative frames from a candidate clip for semantic review."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
        capture_output=True, text=True, timeout=45,
    )
    if probe.returncode != 0:
        raise RuntimeError("Não foi possível medir a duração do clipe candidato.")
    duration = max(0.5, float(probe.stdout.strip()))
    frames = []
    for index, fraction in enumerate((0.25, 0.65), 1):
        frame_path = Path(output_dir) / f"{prefix}_frame_{index}.jpg"
        timestamp = min(max(0.1, duration * fraction), max(0.1, duration - 0.1))
        result = subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{timestamp:.3f}", "-i", str(video_path),
             "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "5", str(frame_path)],
            capture_output=True, text=True, timeout=45,
        )
        if result.returncode == 0 and frame_path.exists() and frame_path.stat().st_size:
            frames.append(str(frame_path))
    if not frames:
        raise RuntimeError("Não foi possível extrair quadros do clipe candidato.")
    return frames

def _search_stock_compatible(query, coverr_key="", pixabay_key="", pexels_key="", per_page=20, exclude_urls=None, relevance_query=None, min_relevance=1.5, style_query="", wikimedia_enabled=False):
    """Search all configured libraries while tolerating an older deployed assets module."""
    try:
        search_parameters = inspect.signature(search_video_sources).parameters
        supports_pexels = "pexels_key" in search_parameters
        supports_style_query = "style_query" in search_parameters
        supports_wikimedia = "wikimedia_enabled" in search_parameters
    except (TypeError, ValueError):
        supports_pexels = False
        supports_style_query = False
        supports_wikimedia = False

    if supports_pexels:
        return search_video_sources(
            query, coverr_key, pixabay_key, pexels_key=pexels_key,
            per_page=per_page, exclude_urls=exclude_urls,
            relevance_query=relevance_query, min_relevance=min_relevance,
            **({"style_query": style_query} if supports_style_query else {}),
            **({"wikimedia_enabled": wikimedia_enabled} if supports_wikimedia else {}),
        )

    # Compatibility path for a Streamlit worker that still has the previous
    # search_video_sources signature loaded in memory.
    candidates, errors = search_video_sources(
        query, coverr_key, pixabay_key, per_page=per_page,
        exclude_urls=exclude_urls, relevance_query=relevance_query,
        min_relevance=min_relevance,
        **({"style_query": style_query} if supports_style_query else {}),
    )
    if pexels_key:
        try:
            response = requests.get(
                "https://api.pexels.com/v1/videos/search",
                headers={"Authorization": pexels_key},
                params={"query": query, "orientation": "portrait", "locale": "pt-BR", "per_page": min(int(per_page), 80)},
                timeout=45,
            )
            response.raise_for_status()
            for item in response.json().get("videos", []):
                files = [
                    vf for vf in item.get("video_files", [])
                    if vf.get("link") and vf.get("file_type") == "video/mp4"
                    and int(vf.get("width") or 0) >= 480 and int(vf.get("height") or 0) >= 700
                ]
                if not files:
                    continue
                files.sort(key=lambda vf: (str(vf.get("quality", "")).lower() in {"hd", "uhd"}, int(vf.get("width") or 0) * int(vf.get("height") or 0)), reverse=True)
                chosen = files[0]
                user = item.get("user") or {}
                candidates.append({
                    "url": chosen["link"], "width": int(chosen.get("width") or 0),
                    "height": int(chosen.get("height") or 0),
                    "vertical": int(chosen.get("height") or 0) > int(chosen.get("width") or 0),
                    "title": item.get("alt") or "", "description": item.get("alt") or "",
                    "source": "Pexels", "source_url": item.get("url") or "https://www.pexels.com/videos/",
                    "author": user.get("name") or "", "author_url": user.get("url") or "",
                })
        except Exception as exc:
            errors.append(f"Pexels: {exc}")

    # Preserve scene relevance when combining fallback Pexels results.
    terms = {word.lower() for word in str(relevance_query or query).split() if len(word) > 2}
    def relevance(item):
        text = (str(item.get("title", "")) + " " + str(item.get("description", ""))).lower()
        matches = sum(1 for term in terms if term in text)
        return (matches, bool(item.get("vertical")), int(item.get("height") or 0), int(item.get("width") or 0))
    deduped = {}
    for item in candidates:
        url = item.get("url")
        if url and url not in set(exclude_urls or []):
            deduped.setdefault(url, item)
    return sorted(deduped.values(), key=relevance, reverse=True), errors


def secret(name, default=""):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)

st.set_page_config(page_title="NEXUS VIDEO STUDIO", page_icon="🎬", layout="wide", initial_sidebar_state="collapsed")

from nexus.visual_styles import STYLE_OPTIONS, STYLE_META, STYLE_PROFILES

@st.dialog("Escolher narração", width="medium", icon=":material/record_voice_over:")
def open_voice_picker():
    import base64

    api_key = secret("FISH_API_KEY")
    if not api_key:
        st.warning("A narração ainda não está conectada. Configure FISH_API_KEY nos Secrets do Streamlit.")
        return

    catalog_key = "nexus_curated_voice_catalog_v1"
    if catalog_key not in st.session_state:
        try:
            with st.spinner("Carregando as 40 vozes cadastradas..."):
                st.session_state[catalog_key] = fish_audio.list_curated_voice_catalog(api_key, max_workers=8)
        except Exception as exc:
            st.session_state[catalog_key] = {"error": str(exc)}

    catalog = st.session_state[catalog_key]
    if isinstance(catalog, dict) and catalog.get("error"):
        st.error(f"Não foi possível carregar as vozes: {catalog['error']}")
        if st.button("Tentar novamente", width="stretch"):
            st.session_state.pop(catalog_key, None)
            st.rerun(scope="fragment")
        return

    categories = ("CapCut", "ElevenLabs", "Licenciadas Fish")
    total_voices = sum(len(catalog.get(category, [])) for category in categories)
    st.caption(
        f"{total_voices} vozes cadastradas · toque em um nome para ouvir a amostra. "
        "Depois, confirme para usar a voz no vídeo."
    )
    current_id = st.session_state.get("nexus_fish_voice_id", "")
    pending_id = st.session_state.get("nexus_pending_voice_id")
    pending_source = st.session_state.get("nexus_pending_voice_preview_source")
    pending_name = st.session_state.get("nexus_pending_voice_name")

    # Preview is a staging choice. The production voice changes only after confirmation.
    if pending_id and pending_source:
        st.markdown(f"**Prévia selecionada: {pending_name}**")
        st.audio(pending_source, format="audio/mp3", autoplay=True)
        if st.button(
            f"✓ Confirmar voz {pending_name.split(' · ')[-1]}",
            type="primary",
            width="stretch",
            key="nexus-confirm-pending-voice",
        ):
            st.session_state["nexus_fish_voice_id"] = pending_id
            st.session_state["nexus_fish_voice_name"] = pending_name
            for key in (
                "nexus_pending_voice_id",
                "nexus_pending_voice_preview_source",
                "nexus_pending_voice_name",
            ):
                st.session_state.pop(key, None)
            st.rerun()

    for category in categories:
        category_voices = catalog.get(category, [])
        if not category_voices:
            continue
        with st.expander(f"{category} · {len(category_voices)} vozes", expanded=True):
            for item in category_voices:
                voice_id = item["id"]
                voice_title = item.get("title") or f"Voz {voice_id[:8]}"
                selected = voice_id == current_id
                pending = voice_id == pending_id
                label = f"{'✓ ' if selected else ''}{'▶ ' if pending else ''}{voice_title}"
                if st.button(
                    label,
                    type="primary" if pending else "secondary",
                    width="stretch",
                    key=f"nexus-preview-select-voice-{voice_id}",
                    help=f"Ouvir prévia · {category} · {voice_title}",
                ):
                    preview_key = f"nexus_voice_preview_audio_{voice_id}"
                    preview_audio = st.session_state.get(preview_key)
                    sample_audio = item.get("sample_audio") or ""
                    try:
                        if preview_audio:
                            preview_source = base64.b64decode(preview_audio)
                        elif sample_audio.startswith("data:audio/") and "," in sample_audio:
                            preview_source = base64.b64decode(sample_audio.split(",", 1)[1])
                        elif sample_audio.startswith(("https://", "http://")):
                            preview_source = sample_audio
                        else:
                            with st.spinner(f"Preparando amostra de {voice_title}..."):
                                audio_bytes = fish_audio.generate_fish_preview(api_key, voice_id)
                            st.session_state[preview_key] = base64.b64encode(audio_bytes).decode("ascii")
                            preview_source = audio_bytes

                        st.session_state["nexus_pending_voice_id"] = voice_id
                        st.session_state["nexus_pending_voice_preview_source"] = preview_source
                        st.session_state["nexus_pending_voice_name"] = f"{category} · {voice_title}"
                        st.rerun(scope="fragment")
                    except Exception as exc:
                        for key in (
                            "nexus_pending_voice_id",
                            "nexus_pending_voice_preview_source",
                            "nexus_pending_voice_name",
                        ):
                            st.session_state.pop(key, None)
                        st.error(f"Não foi possível preparar a amostra de {voice_title}: {str(exc)[:180]}")

    if total_voices != 40:
        st.warning(
            f"O catálogo retornou {total_voices} de 40 vozes cadastradas. "
            "As opções com metadados indisponíveis continuam selecionáveis."
        )
    st.caption("A voz usada na produção só muda ao tocar em “Confirmar voz”.")


@st.dialog("Duração do vídeo", width="small", icon=":material/schedule:")
def open_duration_picker():
    st.caption("Toque no tempo desejado. A escolha é aplicada imediatamente.")
    current = int(st.session_state.get("nexus_duration", 45))
    for row in ((40, 45), (50, 60)):
        cols = st.columns(2, gap="small")
        for col, seconds in zip(cols, row):
            with col:
                if st.button(
                    f"{seconds}s",
                    type="primary" if seconds == current else "secondary",
                    width="stretch",
                    key=f"nexus-duration-option-{seconds}",
                ):
                    st.session_state["nexus_duration"] = seconds
                    st.rerun()


def style_preview_svg(style):
    sky, accent, ground, _ = STYLE_META[style]
    # A visual-language sample, not a scene template: abstract treatments only.
    art = {
        "Quântico & Cósmico": '<g fill="none" stroke="{a}" opacity=".8"><ellipse cx="240" cy="135" rx="190" ry="55"/><ellipse cx="240" cy="135" rx="125" ry="105" transform="rotate(35 240 135)"/><ellipse cx="240" cy="135" rx="125" ry="105" transform="rotate(-35 240 135)"/></g><g fill="{a}"><circle cx="240" cy="135" r="8"/><circle cx="95" cy="55" r="3"/><circle cx="390" cy="72" r="2"/><circle cx="360" cy="210" r="3"/></g>',
        "Sonho Lúcido": '<g opacity=".72"><ellipse cx="155" cy="100" rx="115" ry="70" fill="{a}" opacity=".24"/><ellipse cx="300" cy="155" rx="150" ry="88" fill="{a}" opacity=".2"/><path d="M0 190 C90 80 170 250 260 120 S410 90 480 30" fill="none" stroke="{a}" stroke-width="5" opacity=".8"/></g>',
        "Dark Psychology": '<g><path d="M0 0H290L160 270H0Z" fill="#050609" opacity=".9"/><path d="M480 0H350L225 270H480Z" fill="#050609" opacity=".7"/><path d="M310 0L205 270" stroke="{a}" stroke-width="3" opacity=".75"/><ellipse cx="260" cy="130" rx="80" ry="110" fill="url(#glow)" opacity=".45"/></g>',
        "Épico Espiritual": '<g stroke="{a}" fill="none" opacity=".72"><path d="M240 25L25 270M240 25L455 270M240 25V270" stroke-width="3"/><path d="M110 270L240 70L370 270M55 270L240 120L425 270"/></g><circle cx="240" cy="78" r="48" fill="url(#glow)"/>',
        "Aura Neon": '<g fill="none" stroke="{a}" stroke-width="5" opacity=".85"><circle cx="240" cy="135" r="85"/><circle cx="240" cy="135" r="58"/><path d="M35 180C120 20 360 20 445 180M35 90C120 250 360 250 445 90"/></g>',
        "Hermetismo Clássico": '<g fill="none" stroke="{a}" opacity=".78"><circle cx="240" cy="135" r="104" stroke-width="3"/><circle cx="240" cy="135" r="72"/><path d="M240 25V245M130 135H350M162 57L318 213M318 57L162 213" stroke-width="2"/><path d="M240 42L260 115L333 135L260 155L240 228L220 155L147 135L220 115Z"/></g>',
        "Visual ASMR / Hipnótico": '<g fill="none" stroke="{a}" opacity=".82"><path d="M0 170Q80 35 160 170T320 170T480 170" stroke-width="12"/><path d="M0 205Q80 70 160 205T320 205T480 205" stroke-width="4"/><path d="M0 125Q80 -10 160 125T320 125T480 125" stroke-width="2"/></g>',
        "Cinematográfico": '<g fill="{a}" opacity=".28"><circle cx="95" cy="65" r="38"/><circle cx="380" cy="72" r="55"/><circle cx="330" cy="215" r="25"/></g><path d="M0 220L190 0H285L95 270Z" fill="{a}" opacity=".14"/><path d="M0 245L210 0" stroke="{a}" stroke-width="2" opacity=".55"/>',
        "Dark Cinematográfico": '<path d="M0 0H230L95 270H0ZM480 0H370L250 270H480Z" fill="#05070b" opacity=".9"/><path d="M320 0L205 270" stroke="{a}" stroke-width="4" opacity=".8"/><ellipse cx="255" cy="135" rx="70" ry="125" fill="url(#glow)" opacity=".3"/>',
        "Ilustração Editorial": '<g><path d="M40 35L240 20L190 245L30 220Z" fill="{a}" opacity=".75"/><circle cx="335" cy="95" r="72" fill="{a}" opacity=".3"/><path d="M245 150L440 65L420 245L255 230Z" fill="{a}" opacity=".5"/><path d="M55 235L430 35" stroke="#17151b" stroke-width="5" opacity=".6"/></g>',
        "Filme Noir": '<g fill="none" stroke="{a}" opacity=".75"><path d="M-20 35L160 0M-20 75L205 0M-20 115L250 0M230 270L500 125M275 270L500 170M320 270L500 215" stroke-width="12"/></g><ellipse cx="245" cy="130" rx="90" ry="120" fill="url(#glow)" opacity=".25"/>',
        "Aquarela Artística": '<g opacity=".58"><path d="M35 150C15 65 120 20 190 72S280 210 200 240S45 230 35 150Z" fill="{a}"/><path d="M200 70C250 0 420 35 440 125S380 250 290 220S160 145 200 70Z" fill="{a}" opacity=".55"/><path d="M45 195Q160 115 245 190T455 150" fill="none" stroke="{a}" stroke-width="8"/></g>',
        "Fantasia Cinematográfica": '<g fill="none" stroke="{a}" opacity=".7"><path d="M0 210L100 95L175 185L265 55L370 190L445 100L500 220" stroke-width="8"/><path d="M0 245Q120 170 240 235T480 220" stroke-width="3"/></g><circle cx="265" cy="75" r="60" fill="url(#glow)" opacity=".5"/>',
        "Graphic Novel": '<defs><pattern id="dots" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.7" fill="{a}" opacity=".6"/></pattern></defs><path d="M0 0H300L190 270H0Z" fill="{a}" opacity=".28"/><path d="M300 0H480V270H190Z" fill="url(#dots)"/><path d="M0 220L480 45" stroke="{a}" stroke-width="9"/><path d="M0 242L480 67" stroke="#050505" stroke-width="3"/>',
        "Minimalista Clean": '<g fill="none" stroke="{a}" stroke-width="3"><circle cx="240" cy="135" r="72"/><path d="M240 25V245M130 135H350"/></g><circle cx="240" cy="135" r="24" fill="{a}" opacity=".72"/>',
        "Realismo Humano Emocional": '<ellipse cx="240" cy="135" rx="105" ry="125" fill="url(#glow)" opacity=".65"/><path d="M80 270Q115 170 240 170T400 270" fill="none" stroke="{a}" stroke-width="5" opacity=".65"/><path d="M140 0Q240 70 340 0" fill="none" stroke="{a}" stroke-width="2" opacity=".5"/>',
        "Reconstituição Histórica": '<g fill="none" stroke="{a}" opacity=".8"><path d="M75 245V85Q75 25 135 25Q195 25 195 85V245M285 245V85Q285 25 345 25Q405 25 405 85V245" stroke-width="9"/><path d="M45 245H435M110 110H160M320 110H370" stroke-width="3"/></g><path d="M0 0H480V270H0Z" fill="url(#grain)" opacity=".3"/>',
        "Natureza Contemplativa": '<g fill="none" stroke="{a}" opacity=".75"><path d="M0 200Q90 110 180 195T360 180T480 150" stroke-width="6"/><path d="M0 235Q110 150 220 230T480 205" stroke-width="3"/><path d="M240 40Q180 105 240 160Q300 105 240 40Z" stroke-width="3"/></g><circle cx="240" cy="95" r="65" fill="url(#glow)" opacity=".3"/>',
    }
    drawing = art.get(style, art["Cinematográfico"]).format(a=accent)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="270" viewBox="0 0 480 270">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{sky}"/><stop offset="1" stop-color="{ground}"/></linearGradient>
        <radialGradient id="glow"><stop stop-color="{accent}" stop-opacity=".8"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>
        <pattern id="grain" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{accent}" opacity=".16"/></pattern>
      </defs>
      <rect width="480" height="270" fill="url(#bg)"/>
      <rect width="480" height="270" fill="url(#glow)" opacity=".2"/>
      {drawing}
      <rect width="480" height="270" fill="url(#grain)"/>
      <rect x="5" y="5" width="470" height="260" rx="13" fill="none" stroke="{accent}" stroke-opacity=".45" stroke-width="3"/>
    </svg>'''
    return svg

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root{color-scheme:dark}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:#09090B!important;color:#F4F4F5!important;font-family:'Plus Jakarta Sans',sans-serif!important}
[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 50% 0%,#18122B 0%,#09090B 46%)!important}
[data-testid="stSidebar"],[data-testid="collapsedControl"],[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="manage-app-button"],[data-testid="stFooter"],[data-testid="stBottom"],#MainMenu,header,footer,.stApp>footer,div[class*="viewerBadge"],div[class*="ViewerBadge"],div[class*="viewer-badge"]{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;padding:0!important;margin:0!important;border:0!important}
.block-container{padding-top:1rem!important;padding-bottom:8rem!important;max-width:1280px!important}
.nexus-hero{position:relative;overflow:hidden;padding:1.45rem 1.65rem;border:1px solid #30234d;border-radius:22px;background:linear-gradient(115deg,rgba(24,18,43,.98),rgba(18,18,22,.96) 65%,rgba(30,24,52,.95));box-shadow:0 18px 48px rgba(0,0,0,.38),inset 0 1px 0 rgba(255,255,255,.06);margin-bottom:1rem}
.st-key-nexus-header{position:relative!important;width:100%!important;min-height:4.1rem!important;margin:0 0 .35rem!important}
.nexus-brand-lockup{display:flex;align-items:center;justify-content:center;gap:.72rem;width:100%;min-width:0;margin:0 auto .12rem}
.nexus-brand-lockup svg{display:block;width:48px!important;height:58px!important;flex:0 0 48px!important;object-fit:contain;filter:drop-shadow(0 0 10px rgba(167,139,250,.4))}
.nexus-brand-name{font-family:Georgia,serif!important;font-size:1.8rem!important;letter-spacing:.035em!important;font-weight:700!important;color:#f4f4f5!important;white-space:nowrap}
.st-key-nexus-header .st-key-nexus-open-settings{position:absolute!important;right:.1rem!important;top:.25rem!important;z-index:5!important;width:42px!important}
.st-key-nexus-open-settings button{width:42px!important;height:42px!important;min-height:42px!important;border-radius:50%!important;background:#24232b!important;border:1px solid #38343f!important;font-size:1.2rem!important;padding:0!important}
.nexus-prompt-label,.nexus-section-label{font-size:.78rem;letter-spacing:.12em;font-weight:750;color:#aaa0c5;margin:0 0 .65rem}
.nexus-control-eyebrow{font-size:.68rem;letter-spacing:.1em;font-weight:750;color:#a78bfa;margin:0 0 .5rem}
.nexus-preview-stage{width:min(100%,340px);aspect-ratio:9/16;min-height:0;border:1px solid #51416e;border-radius:22px;background:linear-gradient(145deg,#1a1920,#121116);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:.75rem;margin:.6rem auto 1rem;padding:1rem;box-sizing:border-box;box-shadow:inset 0 0 42px rgba(124,58,237,.06)}
.nexus-preview-stage svg{width:24%;height:auto;max-height:26%;opacity:.75}
.nexus-preview-caption{text-align:center;color:#aaa5b4;font-size:.85rem;line-height:1.45;letter-spacing:.01em}
.st-key-nexus-video-stage{margin-top:.25rem}
.st-key-nexus-compact-controls{display:block!important;width:100%!important;max-width:100%!important;min-width:0!important;overflow:hidden!important;margin:.35rem 0 .8rem!important;box-sizing:border-box!important}
.st-key-nexus-compact-controls [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;align-items:stretch!important;gap:.65rem!important;width:100%!important;max-width:100%!important;min-width:0!important;margin:0!important;box-sizing:border-box!important}
.st-key-nexus-compact-controls [data-testid="column"]{display:block!important;flex:none!important;width:auto!important;max-width:100%!important;min-width:0!important;padding:0!important;box-sizing:border-box!important}
.st-key-nexus-compact-controls [data-testid="stButton"],.st-key-nexus-compact-controls [data-testid="stButton"]>div{display:block!important;width:100%!important;max-width:100%!important;min-width:0!important;box-sizing:border-box!important}
.st-key-nexus-compact-controls [data-testid="stButton"] button{display:flex!important;justify-content:center!important;width:100%!important;max-width:100%!important;min-width:0!important;min-height:3.45rem!important;height:3.45rem!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;border:1px solid #51416e!important;border-radius:13px!important;background:linear-gradient(135deg,#1b1924,#15141b)!important;color:#f4f0ff!important;font-size:.82rem!important;font-weight:650!important;padding:.55rem .45rem!important;box-sizing:border-box!important}
.st-key-nexus-compact-controls [data-testid="stButton"] button:hover{border-color:#9b7bff!important;background:#211b31!important}
.st-key-nexus-video-stage [data-testid="stVerticalBlock"]{gap:0!important}

.nexus-logo-mark{display:grid;place-items:center;width:clamp(58px,16vw,76px);height:clamp(58px,16vw,76px);flex:0 0 auto;border-radius:18px;background:linear-gradient(145deg,#21163e,#101019);border:1px solid #6245a2;box-shadow:0 0 28px rgba(139,92,246,.22),inset 0 1px 0 rgba(255,255,255,.12)}.nexus-logo-mark svg{width:66%;height:66%;filter:drop-shadow(0 0 9px rgba(167,139,250,.45))}
.nexus-brand-name{font-size:clamp(1.55rem,6.2vw,2.25rem);font-weight:700;letter-spacing:.03em;color:#f4f4f5;white-space:nowrap}
.nexus-kicker{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:#a78bfa;font-weight:800;margin:0 0 .8rem}
.nexus-preview{display:flex;gap:13px;align-items:center;padding:12px;border:1px solid #30234d;border-radius:15px;background:linear-gradient(140deg,rgba(124,58,237,.12),rgba(18,18,22,.7));margin:.4rem 0 .8rem}
.nexus-preview img{width:136px;max-width:42%;aspect-ratio:16/9;object-fit:cover;border-radius:10px}
.nexus-preview-title{font-weight:750;color:#fafafa;margin-bottom:4px}
.nexus-preview-copy{font-size:.8rem;color:#a1a1aa;line-height:1.45}
[data-testid="stVerticalBlockBorderWrapper"]>div{background-color:rgba(18,18,22,.85)!important;backdrop-filter:blur(12px)!important;border:1px solid #27272A!important;border-radius:16px!important;padding:1.1rem!important;box-shadow:0 10px 30px rgba(0,0,0,.3)!important}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stSelectbox"] div[data-baseweb="select"],[data-testid="stMultiSelect"] div[data-baseweb="select"]{background:#18181B!important;border:1px solid #27272A!important;border-radius:10px!important;color:#FAFAFA!important;transition:border-color .2s ease,box-shadow .2s ease!important}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus,[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within{border-color:#8B5CF6!important;box-shadow:0 0 0 1px #8B5CF6!important}
[data-testid="stTextArea"] textarea{line-height:1.55!important;min-height:112px!important}
.st-key-nexus-bottom-nav{position:fixed!important;z-index:9999!important;left:0!important;right:0!important;bottom:0!important;width:100%!important;padding:.45rem .7rem!important;background:rgba(12,12,18,.97)!important;border-top:1px solid #30234d!important;border-bottom:1px solid #30234d!important;backdrop-filter:blur(18px)!important}
.st-key-nexus-bottom-nav [data-testid="stPills"]{margin:0!important}
.st-key-nexus-bottom-nav [data-testid="stPills"] [role="group"]{display:flex!important;flex-wrap:nowrap!important;overflow-x:auto!important;justify-content:space-between!important;gap:.35rem!important;scrollbar-width:none!important}
.st-key-nexus-bottom-nav [data-testid="stPills"] button{flex:1 0 auto!important;min-width:max-content!important;justify-content:center!important;padding:.45rem .5rem!important;border-radius:12px!important;font-size:.76rem!important}
[data-testid="stPills"]{width:100%!important;min-width:0!important}
[data-testid="stPills"] [role="group"]{display:flex!important;flex-wrap:nowrap!important;overflow-x:auto!important;gap:.5rem!important;padding:.3rem .1rem .65rem!important;scrollbar-width:thin!important;overscroll-behavior-x:contain!important}
[data-testid="stPills"] [role="group"] button{flex:0 0 auto!important;width:auto!important;min-width:max-content!important;max-width:none!important;white-space:nowrap!important;word-break:keep-all!important;overflow-wrap:normal!important;writing-mode:horizontal-tb!important;padding:.5rem .9rem!important;border:1px solid #34303f!important;border-radius:999px!important;background:#18181d!important;color:#d4d4d8!important}
[data-testid="stPills"] [role="group"] button[aria-pressed="true"]{border-color:#8b5cf6!important;background:rgba(124,58,237,.24)!important;color:#fff!important;box-shadow:0 0 0 1px rgba(139,92,246,.25)!important}
.nexus-output-placeholder{width:min(100%,220px);aspect-ratio:9/16;margin:1rem auto;border:1px solid #4b3b70;border-radius:22px;background:linear-gradient(145deg,#181522,#101014);display:flex;align-items:center;justify-content:center;text-align:center;color:#85808f;padding:1.2rem;box-shadow:inset 0 0 45px rgba(124,58,237,.08)}
.nexus-output-placeholder strong{display:block;color:#d4c5ff;margin-bottom:.5rem;font-size:1rem}
[data-testid="stWidgetLabel"] p,label,[data-testid="stMarkdownContainer"] strong{color:#F4F4F5!important}
[data-testid="stCaptionContainer"],.stCaption{color:#A1A1AA!important}
div[data-testid="stButton"] button{background:#1b1b22!important;color:#e4e4e7!important;border:1px solid #34343d!important;border-radius:11px!important;min-height:2.7rem!important;font-weight:650!important;transition:all .18s ease!important;box-shadow:none!important}
div[data-testid="stButton"] button:hover{border-color:#8B5CF6!important;color:#fff!important;transform:translateY(-1px)!important}
div[data-testid="stButton"] button[kind="primary"]{background:linear-gradient(135deg,#6366F1 0%,#8B5CF6 100%)!important;color:#fff!important;border:0!important;border-radius:12px!important;font-weight:800!important;box-shadow:0 4px 20px rgba(124,58,237,.35)!important}
div[data-testid="stButton"] button[kind="primary"]:hover{box-shadow:0 8px 25px rgba(124,58,237,.5)!important}
[data-testid="stExpander"]{border:1px solid #27272A!important;border-radius:13px!important;background:rgba(24,24,27,.72)!important;overflow:hidden!important}
[data-testid="stExpander"] summary{color:#F4F4F5!important;font-weight:650!important}
[data-testid="stAudio"]{border-radius:12px!important;overflow:hidden!important}
[data-testid="stVideo"]{max-width:320px!important;margin:0 auto!important;border-radius:24px!important;overflow:hidden!important;border:3px solid #27272A!important;box-shadow:0 20px 50px rgba(0,0,0,.7)!important}
[data-testid="stAlert"]{border-radius:13px!important}
[data-testid="stProgress"]>div>div{background:linear-gradient(90deg,#6366F1,#8B5CF6)!important}
hr{border-color:#27272A!important}
@media(max-width:850px){.block-container{padding:.75rem .8rem 8rem!important}.nexus-hero{padding:1rem .7rem;border-radius:17px}.st-key-nexus-header{min-height:3.7rem!important;margin-bottom:.25rem!important}.nexus-brand-lockup{gap:.55rem}.nexus-brand-lockup svg{width:42px!important;height:50px!important;flex-basis:42px!important}.nexus-brand-name{font-size:1.5rem!important}.st-key-nexus-header .st-key-nexus-open-settings{right:0!important;top:.1rem!important}.nexus-preview-stage{width:min(100%,300px)}.st-key-nexus-compact-controls [data-testid="stButton"] button{font-size:.76rem!important;padding:.5rem .45rem!important}}
</style>
""", unsafe_allow_html=True)

NEXUS_MARK_SVG = (Path(__file__).parent / "assets" / "nexus-mark.svg").read_text(encoding="utf-8")

with st.container(key="nexus-header"):
    st.markdown(f"""
    <div class="nexus-brand-lockup">
      {NEXUS_MARK_SVG}
      <span class="nexus-brand-name">NEXUS</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("⚙", key="nexus-open-settings", help="Abrir perfil e configurações"):
        st.session_state["nexus_navigation"] = "♙ Perfil"

# Mobile-first navigation; icon labels follow the supplied reference.
nav_map = {"＋ Criar": "Criar", "▱ Biblioteca": "Biblioteca", "▣ Modelos": "Modelos", "♙ Perfil": "Perfil", "⚙ Perfil": "Perfil"}
if st.session_state.get("nexus_navigation") not in nav_map:
    st.session_state["nexus_navigation"] = "＋ Criar"
with st.container(key="nexus-bottom-nav"):
    active_nav = st.pills(
        "Navegação", ["＋ Criar", "▱ Biblioteca", "▣ Modelos", "♙ Perfil"],
        selection_mode="single", default="＋ Criar", key="nexus_navigation",
        label_visibility="collapsed",
    ) or "＋ Criar"
active_view = nav_map.get(active_nav, "Criar")

if active_view == "Criar":
    if "nexus_style" not in st.session_state or st.session_state["nexus_style"] not in STYLE_OPTIONS:
        st.session_state["nexus_style"] = "Cinematográfico"
    
    # Primary creation flow makes the credit-sensitive visual engine visible.
    if st.session_state.get("nexus_render_mode") not in RENDER_MODE_OPTIONS:
        st.session_state["nexus_render_mode"] = default_render_mode()
    render_mode = st.radio(
        "Motor visual",
        RENDER_MODE_OPTIONS,
        horizontal=True,
        key="nexus_render_mode",
        help=(
            "O modo econômico usa bibliotecas de vídeo e evita Cloudflare/Modal. "
            "Gemini e Fish Audio continuam sujeitos às cotas e planos das respectivas contas. "
            "O modo de IA original envia cenas para geração e animação e consome créditos."
        ),
    )
    if mode_uses_modal(render_mode):
        st.warning(
            "IA original usa créditos da Cloudflare e da Modal. O custo total de um vídeo "
            "de 40–50s ainda não foi validado; o limite interno do worker não representa "
            "uma garantia de cobrança máxima do Workspace."
        )
    else:
        st.caption(
            "Modo econômico selecionado: não aciona geração Cloudflare nem GPU Modal. "
            "Chamadas Gemini/Fish Audio ainda dependem das cotas das suas contas."
        )
    with st.container(border=True):
        topic = st.text_area(
            "Assunto ou roteiro", height=92,
            placeholder="Descreva o tema do vídeo ou cole seu roteiro completo...",
            label_visibility="collapsed", key="nexus_topic",
        )
        generate_requested = st.button("Gerar vídeo", type="primary", use_container_width=True, key="nexus-generate-top")

    st.markdown('<div class="nexus-section-label">ESTILO VISUAL</div>', unsafe_allow_html=True)
    with st.container(key="nexus-style-carousel"):
        style = st.pills(
            "Estilo visual", STYLE_OPTIONS, selection_mode="single",
            default=st.session_state["nexus_style"], key="nexus_style",
            label_visibility="collapsed", width="stretch", wrap=False,
        ) or st.session_state["nexus_style"]

    fish_api_key = secret("FISH_API_KEY")
    if "nexus_fish_voice_id" not in st.session_state:
        st.session_state["nexus_fish_voice_id"] = secret("FISH_VOICE_ID")
    if "nexus_fish_voice_name" not in st.session_state:
        st.session_state["nexus_fish_voice_name"] = ""
    st.session_state.setdefault("nexus_duration", 45)
    selected_voice_name = st.session_state.get("nexus_fish_voice_name") or ""
    voice_button_label = selected_voice_name.split(" · ")[-1] if selected_voice_name else "Escolher voz"
    if len(voice_button_label) > 19:
        voice_button_label = voice_button_label[:18].rstrip() + "…"
    duration = int(st.session_state.get("nexus_duration", 45))

    with st.container(key="nexus-compact-controls"):
        voice_col, duration_col = st.columns([1, 1], gap="small", vertical_alignment="center")
        with voice_col:
            if st.button(f"🎙️  {voice_button_label}", key="nexus-open-voice-picker", width="stretch"):
                open_voice_picker()
        with duration_col:
            if st.button(f"◷  {duration}s", key="nexus-open-duration-picker", width="stretch"):
                open_duration_picker()

    voice = st.session_state.get("nexus_fish_voice_id", "")

    # Fixed-position slot in the creation flow: planning and render feedback
    # are populated here instead of appearing far below the preview.
    status_slot = st.empty()

    if generate_requested:

        # Remove any previous result first: a failed new request must never leave
        # an old 44s storyboard visible as if it were the latest response.
        st.session_state.pop("nexus_plan", None)
        st.session_state.pop("nexus_errors", None)
        st.session_state.pop("nexus_rendered_video", None)
        st.session_state.pop("nexus_rendered_info", None)
    
        if not topic.strip():
            st.error("Informe um assunto ou roteiro.")
        elif not secret("GEMINI_API_KEY"):
            st.error("O serviço de direção ainda não está conectado.")
        else:
            with st.spinner(
                f"Desenvolvendo o roteiro com liberdade editorial (referência {duration}s, limite {int(duration) + 10}s) e planejando as cenas..."
            ):
                try:
                    plan = create_storyboard(topic, style, duration, secret)
                    errors = validate_storyboard(plan, duration)
                    actual_duration = float(plan.get(
                        "estimated_duration_seconds",
                        sum(float(scene.get("duration_seconds", 0) or 0) for scene in plan.get("scenes", [])),
                    ))
                    if errors:
                        raise RuntimeError(
                            "O diretor não entregou um roteiro válido: " + " ".join(errors)
                        )
                    st.session_state["nexus_plan"] = plan
                    st.session_state["nexus_errors"] = []
                    st.success(
                        f"Planejamento criado: {len(plan['scenes'])} cenas · "
                        f"estimativa de {actual_duration:.0f}s · "
                        f"referência {int(duration)}s · limite {int(duration) + 10}s. "
                        "A duração final será definida pela narração real da voz selecionada."
                    )
                except Exception as exc:
                    st.error(str(exc))
    
    if "nexus_plan" in st.session_state:
        plan = st.session_state["nexus_plan"]
        ready_scenes = plan.get("scenes", [])
        ready_duration = sum(float(scene.get("duration_seconds", 0) or 0) for scene in ready_scenes)
        status_slot.info(
            f"Planejamento pronto · {len(ready_scenes)} cenas · estimativa {ready_duration:.0f}s. "
            f"Referência {int(plan.get('requested_duration_seconds', duration))}s · "
            f"limite {int(plan.get('maximum_duration_seconds', int(duration) + 10))}s. "
            "O vídeo final acompanhará a duração real da narração, sem esticar a voz."
        )
        scenes = plan.get("scenes", [])
        total_seconds = sum(float(scene.get("duration_seconds", 0) or 0) for scene in scenes)
        with st.expander(
            f"Ver planejamento completo · {len(scenes)} cenas · {total_seconds:.0f}s",
            expanded=False,
        ):
            st.markdown("### Direção audiovisual")
            st.write(plan.get("topic_interpretation", ""))
            st.write(plan.get("creative_thesis", ""))
            if plan.get("hook"):
                st.markdown("**Hook de abertura**")
                st.write(plan["hook"])
            if plan.get("retention_strategy"):
                st.markdown("**Estratégia de retenção**")
                st.write(plan["retention_strategy"])
            if plan.get("cta"):
                st.markdown("**CTA integrado à narração**")
                st.write(plan["cta"])
            seo = plan.get("seo", {})
            if seo:
                st.markdown("### SEO baseado no roteiro")
                st.write("**Palavra-chave principal:** " + str(seo.get("primary_keyword", "")))
                if seo.get("secondary_keywords"):
                    st.write("**Termos secundários:** " + ", ".join(seo["secondary_keywords"]))
                if seo.get("title"):
                    st.write("**Título:** " + seo["title"])
                if seo.get("description"):
                    st.write("**Descrição:** " + seo["description"])
                if seo.get("hashtags"):
                    st.write("**Hashtags:** " + " ".join(seo["hashtags"]))
            if plan.get("director_model"):
                st.caption("Modelo Gemini: " + plan["director_model"])
            st.caption("Estilo visual: " + plan.get("style_lock", style))
            adjustment = plan.get("duration_adjustment")
            if adjustment:
                st.info(
                    f"A IA distribuiu os {adjustment['requested_seconds']} segundos entre as cenas "
                    f"(a estimativa inicial era de {adjustment.get('ai_estimated_seconds', adjustment.get('original_seconds', 0)):.1f}s)."
                )
            preflight = plan.get("preflight_report")
            if isinstance(preflight, dict):
                st.markdown("### Pré-validação audiovisual")
                st.caption(
                    "Checagem heurística de texto/metadados; não analisa os quadros "
                    "e não substitui a revisão visual."
                )
                action_ratio = float(preflight.get("unique_action_ratio", 0) or 0)
                search_ratio = float(preflight.get("unique_search_ratio", 0) or 0)
                action_coverage = float(preflight.get("action_coverage_ratio", 0) or 0)
                motion_coverage = float(preflight.get("motion_prompt_coverage_ratio", 0) or 0)
                physical_motion_coverage = float(preflight.get("motion_action_coverage_ratio", 0) or 0)
                near_action_count = len(preflight.get("near_duplicate_action_pairs", []))
                near_search_count = len(preflight.get("near_duplicate_search_pairs", []))
                st.caption(
                    f"Variedade textual: ações {action_ratio:.0%} · "
                    f"buscas {search_ratio:.0%} · "
                    f"{int(preflight.get('unique_shot_types', 0) or 0)} tipos de plano · "
                    f"{int(preflight.get('unique_settings', 0) or 0)} ambientes distintos."
                )
                st.caption(
                    f"Cobertura: ação descrita {action_coverage:.0%} · "
                    f"movimento descrito {motion_coverage:.0%} · "
                    f"verbo físico reconhecido {physical_motion_coverage:.0%} · "
                    f"possíveis pares semelhantes: {near_action_count} ações / {near_search_count} buscas."
                )
                preflight_warnings = preflight.get("warnings", [])
                if preflight_warnings:
                    st.warning(
                        "Pontos para revisar:\n"
                        + "\n".join(f"• {warning}" for warning in preflight_warnings)
                    )
                else:
                    st.caption(
                        "Nenhuma repetição literal ou alerta de variedade foi detectado "
                        "pelas regras automáticas."
                    )
            st.markdown("### Cenas")
            for i, scene in enumerate(scenes, 1):
                st.markdown(f"**Cena {i} · {scene.get('duration_seconds', 0)}s · {scene.get('purpose', '')}**")
                st.markdown("**Narração**")
                st.write(scene.get("voiceover", ""))
                st.markdown("**Ação visual**")
                st.write(scene.get("visual_action", ""))
                st.markdown("**Estilo visual aplicado**")
                st.write(scene.get("visual_style", plan.get("style_lock", style)))
                if scene.get("style_search_terms"):
                    st.caption("Termos de estilo: " + scene.get("style_search_terms", ""))
                st.markdown("**Correspondência semântica**")
                st.write(scene.get("semantic_reason", ""))
                st.markdown("**Movimento e microeventos**")
                st.write(scene.get("camera_motion", ""))
                st.write(" → ".join(scene.get("motion_events", [])))
                st.caption("Busca visual: " + scene.get("asset_search_query", ""))
                st.divider()
    
        if mode_uses_modal(render_mode):
            brain4_enabled = st.checkbox(
                "Ativar Brain 4 — edição inteligente sincronizada",
                value=False,
                help=(
                    "Faz uma chamada Gemini por vídeo para planejar cortes, legendas, "
                    "efeitos e mixagem usando os timestamps reais da Fish Audio. "
                    "Pode gerar custo de API. Desativado por padrão."
                ),
            )
            st.caption(
                "Antes de uma produção, você pode testar o Brain 4 isoladamente. "
                "O teste usa roteiro e timestamps sintéticos, faz uma geração Gemini "
                "e não inicia Fish Audio, Cloudflare, Modal ou renderização."
            )
            if st.button("Testar Brain 4 — sem produzir vídeo", use_container_width=True):
                smoke_key = secret("GEMINI_API_KEY")
                if not smoke_key:
                    st.error("Configure GEMINI_API_KEY antes do teste. Nenhuma chamada foi feita.")
                else:
                    try:
                        with st.spinner("Executando uma geração Gemini e validando o contrato Brain 4..."):
                            smoke_module = importlib.import_module("nexus.brain4_smoke_test")
                            smoke_module = importlib.reload(smoke_module)
                            smoke_result = smoke_module.run_brain4_live_smoke_test(
                                smoke_key,
                                requested_model=secret("GEMINI_MODEL") or "auto",
                            )
                        st.session_state["nexus_brain4_smoke_result"] = smoke_result
                        st.session_state.pop("nexus_brain4_smoke_error", None)
                    except Exception as smoke_error:
                        st.session_state.pop("nexus_brain4_smoke_result", None)
                        st.session_state["nexus_brain4_smoke_error"] = str(smoke_error)
            smoke_result = st.session_state.get("nexus_brain4_smoke_result")
            if smoke_result:
                st.success("Brain 4 respondeu e a timeline passou pela validação contratual.")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Alinhamento", smoke_result["alignment_level"])
                c2.metric("Legendas", smoke_result["caption_event_count"])
                c3.metric("Âncoras", smoke_result["edit_anchor_count"])
                c4.metric("Mixagem", smoke_result["audio_mix_event_count"])
                st.caption(
                    f"Fixture sintético de {smoke_result['audio_duration_seconds']:.1f}s · "
                    f"{smoke_result['sfx_event_count']} efeitos sonoros · "
                    "nenhum vídeo foi produzido."
                )
            smoke_error = st.session_state.get("nexus_brain4_smoke_error")
            if smoke_error:
                st.error("O teste Brain 4 não foi aprovado: " + smoke_error)
        else:
            brain4_enabled = False
        if st.button("Produzir vídeo completo", type="primary", use_container_width=True):
            coverr_key = ""
            pixabay_key = secret("PIXABAY_API_KEY")
            pexels_key = secret("PEXELS_API_KEY")
            configured_libraries = [
                name for name, key in (
                    ("Wikimedia Commons", True), ("Pixabay", pixabay_key), ("Pexels", pexels_key)
                ) if key
            ]
            if render_mode == ECONOMY_MODE and len(configured_libraries) == 1:
                st.warning(
                    f"Somente {configured_libraries[0]} está configurada. "
                    "O NEXUS fará revisão visual dos clipes, mas a variedade de bibliotecas "
                    "depende de configurar outras fontes."
                )
            if st.session_state.get("nexus_errors"):
                st.error("O storyboard precisa ser corrigido antes da produção.")
            elif brain4_enabled and not secret("GEMINI_API_KEY"):
                st.error("Brain 4 foi ativado, mas GEMINI_API_KEY não está configurada. Nenhum trabalho foi enviado.")
            elif mode_uses_modal(render_mode):
                github_token = secret("GITHUB_ACTIONS_TOKEN")
                cloudflare_token = secret("CLOUDFLARE_API_TOKEN")
                if not github_token or not cloudflare_token or not fish_api_key or not voice:
                    with status_slot.container():
                        st.error("Configure GITHUB_ACTIONS_TOKEN, CLOUDFLARE_API_TOKEN e FISH_API_KEY, e selecione uma voz da biblioteca Fish Audio.")
                        st.info("O repositório GitHub também precisa dos Secrets CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, MODAL_TOKEN_ID e MODAL_TOKEN_SECRET. O worker Modal deve estar implantado. O manifesto e o MP4 trafegam criptografados.")
                else:
                    with status_slot.container():
                        st.markdown("**Produção do vídeo**")
                        st.caption("Acompanhe a etapa atual, o tempo decorrido e a estimativa de conclusão.")
                        progress = st.progress(0.03, text="Preparando envio seguro do storyboard...")
                        status_detail = st.empty()

                    def update_worker_progress(message, fraction=0.05, elapsed_seconds=0, remaining_seconds=600):
                        percent = max(1, min(96, int(round(float(fraction) * 100))))
                        elapsed_seconds = max(0, int(elapsed_seconds or 0))
                        remaining_seconds = max(0, int(remaining_seconds or 0))
                        elapsed_label = f"{elapsed_seconds // 60}min {elapsed_seconds % 60:02d}s"
                        remaining_label = f"{remaining_seconds // 60}min" if remaining_seconds else "quase concluído"
                        progress.progress(
                            max(0.01, min(0.96, float(fraction))),
                            text=f"{percent}% · {message}",
                        )
                        status_detail.caption(
                            f"Decorrido: {elapsed_label} · restante estimado: {remaining_label}. "
                            "A porcentagem é aproximada durante as etapas internas da Modal."
                        )

                    try:
                        # Streamlit Cloud may retain stale dependencies after a GitHub sync.
                        # Reload the crypto module first, then reload the renderer that imports it.
                        render_crypto_module = importlib.import_module("nexus.render_crypto")
                        render_crypto_module = importlib.reload(render_crypto_module)
                        if not hasattr(render_crypto_module, "decrypt_compressed_text"):
                            raise RuntimeError(
                                "Módulo de criptografia desatualizado ou incompatível: "
                                "decrypt_compressed_text não está disponível."
                            )
                        github_renderer_module = importlib.import_module("nexus.github_renderer")
                        github_renderer_module = importlib.reload(github_renderer_module)
                        render_on_github = github_renderer_module.render_on_github

                        result = render_on_github(
                            plan, voice, github_token, encryption_secret=cloudflare_token,
                            fish_api_key=fish_api_key,
                            fish_voice_id=voice,
                            gemini_api_key=secret("GEMINI_API_KEY"),
                            brain4_enabled=brain4_enabled,
                            gemini_model=secret("GEMINI_MODEL") or "auto",
                            topic=topic,
                            style=style,
                            progress_callback=update_worker_progress
                        )
                        video_bytes = result["video"]
                        report = result.get("report") or {}
                        st.session_state["nexus_rendered_video"] = video_bytes
                        st.session_state["nexus_rendered_filename"] = "nexus_video.mp4"
                        st.session_state["nexus_rendered_info"] = {
                            "duration": float(report.get("duration") or duration),
                            "width": int(report.get("width") or 720),
                            "height": int(report.get("height") or 1280),
                            "video_codec": report.get("video_codec", "h264"),
                            "audio_codec": report.get("audio_codec", ""),
                            "narration_provider": report.get("narration_provider", "não informado pelo worker"),
                            "editorial_pipeline": report.get("editorial_pipeline", {"status": "unknown"}),
                            "size_mb": len(video_bytes) / (1024 * 1024),
                            "scene_count": len(plan.get("scenes", [])),
                            "motion_clip_count": len(report.get("motion_clips") or []),
                            "motion_quality": report.get("motion_quality") or [],
                            "low_motion_scene_count": int(report.get("low_motion_scene_count") or 0),
                            "total_i2v_seconds": float(report.get("total_i2v_seconds") or 0),
                            "total_i2v_inference_seconds": float(report.get("total_i2v_inference_seconds") or 0),
                            "visual_source": report.get("visual_source", "Cloudflare + Modal I2V + Remotion"),
                            "worker_run_id": result.get("run_id"),
                            "visual_reviews": [],
                            "source_credits": [],
                        }
                        motion_diagnostics = st.session_state["nexus_rendered_info"].get("motion_quality") or []
                        if motion_diagnostics:
                            low_motion_count = st.session_state["nexus_rendered_info"]["low_motion_scene_count"]
                            if low_motion_count:
                                st.warning(
                                    f"Diagnóstico de movimento: {low_motion_count} cena(s) tiveram "
                                    "congelamento visual prolongado. Consulte os detalhes antes de publicar."
                                )
                            else:
                                st.caption(
                                    "Diagnóstico de movimento: nenhum congelamento prolongado foi detectado. "
                                    "Isso não substitui a revisão da ação e da aderência à narração."
                                )
                            with st.expander("Diagnóstico técnico de movimento por cena"):
                                st.dataframe([
                                    {
                                        "Cena": item.get("scene_index"),
                                        "Congelamento": (
                                            f'{item.get("freeze_ratio", 0):.0%}'
                                            if item.get("status") == "analyzed" else "Indisponível"
                                        ),
                                        "Maior trecho congelado": (
                                            f'{item.get("longest_freeze_seconds", 0):.2f}s'
                                            if item.get("status") == "analyzed" else "—"
                                        ),
                                        "Diagnóstico": item.get("diagnostic", "Indisponível"),
                                    }
                                    for item in motion_diagnostics
                                ], use_container_width=True, hide_index=True)
                        # Final editorial QA: inspect one representative frame from every scene.
                        # This review is advisory and never discards a technically valid render.
                        try:
                            from nexus.visual_review import extract_scene_frames, review_scene_frames
                            visual_key = secret("GEMINI_API_KEY")
                            if visual_key:
                                with tempfile.TemporaryDirectory(prefix="nexus_visual_review_") as qa_dir:
                                    qa_video = Path(qa_dir) / "rendered.mp4"
                                    qa_video.write_bytes(video_bytes)
                                    frames = extract_scene_frames(qa_video, plan.get("scenes", []), Path(qa_dir) / "frames")
                                    reviews = review_scene_frames(frames, plan.get("scenes", []), visual_key)
                                st.session_state["nexus_rendered_info"]["final_visual_audit"] = reviews
                                semantic_avg = round(sum(item["semantic_score"] for item in reviews) / max(1, len(reviews)), 1)
                                motion_avg = round(sum(item["motion_progression_score"] for item in reviews) / max(1, len(reviews)), 1)
                                continuity_avg = round(sum(item["continuity_score"] for item in reviews) / max(1, len(reviews)), 1)
                                editorial_score = round(semantic_avg * 0.40 + motion_avg * 0.35 + continuity_avg * 0.25, 1)
                                critical_count = sum(len(item["critical_issues"]) for item in reviews)
                                needs_attention = any(
                                    not item["matches_narration"]
                                    or not item["action_observed"]
                                    or item["semantic_score"] < 7
                                    or item["motion_progression_score"] < 7
                                    or item["continuity_score"] < 7
                                    or item["critical_issues"]
                                    for item in reviews
                                )
                                st.session_state["nexus_rendered_info"]["final_visual_review_average"] = semantic_avg
                                st.session_state["nexus_rendered_info"]["final_editorial_quality_score"] = editorial_score
                                st.session_state["nexus_rendered_info"]["visual_review_status"] = (
                                    "needs_attention" if needs_attention else "reviewed"
                                )
                                st.caption(
                                    f"Auditoria editorial Gemini: {editorial_score}/10 "
                                    f"(aderência {semantic_avg}, movimento {motion_avg}, continuidade {continuity_avg}); "
                                    f"{len(reviews)} cenas avaliadas."
                                )
                                if needs_attention:
                                    st.warning(
                                        f"Revisão editorial necessária: {sum(1 for item in reviews if not item['matches_narration'] or not item['action_observed'] or item['semantic_score'] < 7 or item['motion_progression_score'] < 7 or item['continuity_score'] < 7 or item['critical_issues'])} cena(s) "
                                        f"abaixo do padrão e {critical_count} falha(s) crítica(s). Não considere o vídeo aprovado sem revisão."
                                    )
                                with st.expander("Auditoria editorial detalhada por cena"):
                                    st.dataframe([
                                        {
                                            "Cena": item["scene_number"],
                                            "Aderência": f'{item["semantic_score"]}/10',
                                            "Movimento real": f'{item["motion_progression_score"]}/10',
                                            "Ação observável": "Sim" if item["action_observed"] else "Não",
                                            "Continuidade": f'{item["continuity_score"]}/10',
                                            "Progressão temporal": item["temporal_progression"],
                                            "Problemas": "; ".join(item["issues"] + item["critical_issues"]),
                                            "Recomendação": item["recommendation"],
                                        }
                                        for item in reviews
                                    ], use_container_width=True, hide_index=True)
                            else:
                                st.session_state["nexus_rendered_info"]["visual_review_status"] = "not_configured"
                                st.warning("MP4 validado tecnicamente; auditoria visual não executada porque GEMINI_API_KEY não está disponível neste ambiente.")
                        except Exception as review_error:
                            st.session_state["nexus_rendered_info"]["visual_review_status"] = "failed"
                            st.warning(f"MP4 produzido, mas a auditoria visual não pôde ser concluída: {review_error}")
                        progress.progress(1.0, text="100% · Render e verificações concluídos.")
                        status_detail.caption("Concluído · MP4 recuperado e verificações técnicas finalizadas.")
                        st.success("MP4 produzido e verificações técnicas concluídas. A aprovação editorial depende do resultado da auditoria visual.")
                    except Exception as exc:
                        progress.empty()
                        status_detail.error(f"Produção Cloudflare + Remotion interrompida: {exc}")
            elif not configured_libraries:
                st.error("Nenhuma biblioteca de vídeo está disponível para pesquisa.")
            else:
                st.session_state.pop("nexus_rendered_video", None)
                st.session_state.pop("nexus_rendered_info", None)
                work = Path(tempfile.mkdtemp(prefix="nexus_"))
                try:
                    media, missing = [], []
                    used_asset_urls = set()
                    progress = st.progress(0, text="Preparando cenas...")
                    # Streamlit workers may retain a previously imported module after
                    # a partial hot reload. Refresh the director before visual review.
                    import nexus.director as director_module
                    director_module = importlib.reload(director_module)
                    for i, scene in enumerate(plan["scenes"]):
                        progress.progress((i + 1) / (len(plan["scenes"]) + 2), text=f"Buscando clipe para a cena {i + 1}/{len(plan['scenes'])}...")
                        # Enforce the global style at render time too, including storyboards
                        # created before the deterministic style-lock fix was deployed.
                        global_style = plan.get("style_lock", style)
                        style_terms = scene.get("style_search_terms") or global_style
                        scene["visual_style"] = global_style
                        scene["style_search_terms"] = style_terms
                        # Keep scene meaning and visual style as separate search signals.
                        primary_query = scene["asset_search_query"].strip()
                        fallback_query = str(scene.get("fallback_search_query", "")).strip()
                        candidates, source_errors = _search_stock_compatible(
                            primary_query,
                            coverr_key,
                            pixabay_key,
                            pexels_key=pexels_key,
                            exclude_urls=used_asset_urls,
                            relevance_query=scene["asset_search_query"],
                            style_query=style_terms,
                            wikimedia_enabled=True,
                        )
                        if not candidates and fallback_query:
                            candidates, retry_errors = _search_stock_compatible(
                                fallback_query,
                                "",
                                pixabay_key,
                                pexels_key=pexels_key,
                                exclude_urls=used_asset_urls,
                                relevance_query=scene.get("fallback_search_query", scene["asset_search_query"]),
                                style_query=style_terms,
                                wikimedia_enabled=True,
                            )
                            source_errors.extend(retry_errors)
                        if not candidates:
                            missing.append({
                                "scene": i + 1,
                                "query": primary_query,
                                "fallback": fallback_query,
                                "style": style_terms,
                                "sources": [
                                    name for name, configured in (
                                        ("Wikimedia Commons", True),
                                        ("Pixabay", bool(pixabay_key)),
                                        ("Pexels", bool(pexels_key)),
                                    ) if configured
                                ],
                                "errors": source_errors,
                            })
                            continue
                        shortlist = diverse_candidate_shortlist(candidates, limit=12)
                        reviewed_candidates = []
                        candidate_errors = []
                        for candidate_index, candidate in enumerate(shortlist, 1):
                            try:
                                candidate_path = download_file(
                                    candidate["url"],
                                    work / f"review_scene_{i:02d}_candidate_{candidate_index:02d}.mp4",
                                )
                                frame_paths = _extract_visual_review_frames(
                                    candidate_path, work, f"scene_{i:02d}_candidate_{candidate_index:02d}"
                                )
                                reviewed_candidates.append({
                                    "candidate": candidate,
                                    "path": candidate_path,
                                    "frame_paths": frame_paths,
                                })
                            except Exception as candidate_error:
                                candidate_errors.append(
                                    f"{candidate.get('source', 'Biblioteca')}: {candidate_error}"
                                )
                        if not reviewed_candidates:
                            missing.append({
                                "scene": i + 1,
                                "query": primary_query,
                                "fallback": fallback_query,
                                "errors": source_errors + candidate_errors + [
                                    "Nenhum candidato pôde ser baixado e inspecionado."
                                ],
                            })
                            continue
                        progress.progress(
                            (i + 1) / (len(plan["scenes"]) + 2),
                            text=f"IA avaliando a correspondência visual da cena {i + 1}/{len(plan['scenes'])}...",
                        )
                        try:
                            visual_review = director_module.review_visual_candidates(scene, reviewed_candidates, secret)
                        except Exception as review_error:
                            missing.append({
                                "scene": i + 1,
                                "query": primary_query,
                                "fallback": fallback_query,
                                "errors": source_errors + [f"Revisão visual: {review_error}"],
                            })
                            continue
                        selected_index = int(visual_review.get("selected_candidate", 0)) - 1
                        if selected_index < 0 or selected_index >= len(reviewed_candidates):
                            missing.append({
                                "scene": i + 1,
                                "query": primary_query,
                                "fallback": fallback_query,
                                "errors": source_errors + [
                                    "Nenhum clipe atingiu a confiança mínima da avaliação visual. "
                                    + str(visual_review.get("reason", ""))
                                ],
                            })
                            continue
                        chosen_record = reviewed_candidates[selected_index]
                        chosen = chosen_record["candidate"]
                        used_asset_urls.add(chosen["url"])
                        path = work / f"scene_{i:02d}.mp4"
                        shutil.copy2(chosen_record["path"], path)
                        probe = subprocess.run(
                            ["ffprobe", "-v", "error", "-show_entries",
                             "format=duration,size:stream=codec_name,codec_type,width,height",
                             "-of", "json", str(path)],
                            capture_output=True, text=True, timeout=60
                        )
                        if probe.returncode != 0:
                            raise RuntimeError(f"Não foi possível validar o arquivo da cena {i + 1}: {probe.stderr[-1200:]}")
                        metadata = json.loads(probe.stdout)
                        video_stream = next((item for item in metadata.get("streams", []) if item.get("codec_type") == "video"), None)
                        if not video_stream:
                            raise RuntimeError(f"O clipe da cena {i + 1} não contém vídeo.")
                        media.append({
                            "path": str(path),
                            "duration": scene["duration_seconds"],
                            # Library footage already contains real camera/subject motion.
                            # Keep the source movement; do not add a synthetic zoom to every clip.
                            "camera_motion": "preserve",
                            "source_title": chosen.get("title", ""),
                            "source_url": chosen.get("source_url", ""),
                            "source": chosen.get("source", "Stock"),
                            "author": chosen.get("author", ""),
                            "author_url": chosen.get("author_url", ""),
                            "license": chosen.get("license", ""),
                            "license_url": chosen.get("license_url", ""),
                            "credit": chosen.get("credit", ""),
                            "attribution_required": chosen.get("attribution_required", False),
                            "visual_review_confidence": visual_review.get("confidence", 0),
                            "visual_review_semantic_match": visual_review.get("semantic_match", 0),
                            "visual_review_style_match": visual_review.get("style_match", 0),
                            "visual_review_reason": visual_review.get("reason", ""),
                            "source_width": video_stream.get("width"),
                            "source_height": video_stream.get("height"),
                        })
                    if missing:
                        progress.empty()
                        scene_numbers = [item["scene"] for item in missing]
                        st.error(f"Não encontrei clipes para as cenas {scene_numbers}. Interrompi para evitar um vídeo incompleto.")
                        with st.expander("Detalhes das buscas sem resultado"):
                            for item in missing:
                                st.markdown(f"**Cena {item['scene']}**")
                                st.caption("Busca de conteúdo: " + item["query"])
                                st.caption("Estilo solicitado: " + (item.get("style") or "não informado"))
                                st.caption("Bibliotecas configuradas/consultadas: " + (", ".join(item.get("sources") or configured_libraries) or "nenhuma — configure as chaves das APIs"))
                                if item["fallback"]:
                                    st.caption("Busca alternativa: " + item["fallback"])
                                if item["errors"]:
                                    for error in item["errors"]:
                                        st.caption(error)
                                else:
                                    st.caption("As bibliotecas responderam, mas não retornaram candidatos para a busca de conteúdo. O estilo visual, sozinho, não é usado para preencher uma cena.")
                    else:
                        progress.progress((len(plan["scenes"]) + 1) / (len(plan["scenes"]) + 2), text="Gerando narração e montagem...")
                        output = work / "nexus_video.mp4"
                        audio = work / "voice.mp3"
                        target_duration = sum(float(scene["duration_seconds"]) for scene in plan["scenes"])
                        for calibration_attempt in range(3):
                            narration = " ".join(scene["voiceover"] for scene in plan["scenes"])
                            audio, actual_tts_provider = fish_audio.make_voice(
                                narration, voice, audio,
                                fish_api_key=fish_api_key,
                                fish_voice_id=voice,
                                return_provider=True,
                            )
                            st.caption(f"Narração gerada por: {actual_tts_provider}")
                            audio_probe = subprocess.run(
                                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=noprint_wrappers=1:nokey=1", str(audio)],
                                capture_output=True, text=True, timeout=60
                            )
                            if audio_probe.returncode != 0:
                                raise RuntimeError("Não foi possível medir a duração real da narração.")
                            actual_audio_duration = float(audio_probe.stdout.strip())
                            difference_ratio = abs(actual_audio_duration - target_duration) / target_duration
                            if difference_ratio <= 0.10:
                                break
                            if calibration_attempt == 2:
                                raise RuntimeError(
                                    f"A IA revisou a narração, mas a voz ainda ficou com {actual_audio_duration:.1f}s "
                                    f"para uma meta de {target_duration:.1f}s. O texto não será forçado por alteração de velocidade."
                                )
                            progress.progress(
                                (len(plan["scenes"]) + 1) / (len(plan["scenes"]) + 2),
                                text=f"Ajustando o roteiro à duração real da voz ({actual_audio_duration:.1f}s / {target_duration:.1f}s)..."
                            )
                            # Import the optional calibration step lazily so a stale Streamlit
                            # worker cannot prevent the entire studio from starting.
                            try:
                                from nexus.director import revise_narration_for_duration
                            except ImportError as exc:
                                raise RuntimeError(
                                    "O módulo do diretor está desatualizado neste servidor. "
                                    "Reinicie o aplicativo Streamlit para carregar a versão atualizada."
                                ) from exc
                            plan = revise_narration_for_duration(
                                plan, target_duration, actual_audio_duration, topic, style, secret
                            )
                        render_video(media, audio, output)
                        final_probe = subprocess.run(
                            ["ffprobe", "-v", "error", "-show_entries",
                             "format=duration,size:stream=codec_name,codec_type,width,height",
                             "-of", "json", str(output)],
                            capture_output=True, text=True, timeout=60
                        )
                        if final_probe.returncode != 0:
                            raise RuntimeError("O FFmpeg terminou, mas o MP4 final não passou na leitura do FFprobe.")
                        final_metadata = json.loads(final_probe.stdout)
                        final_streams = final_metadata.get("streams", [])
                        final_video = next((item for item in final_streams if item.get("codec_type") == "video"), None)
                        final_audio = next((item for item in final_streams if item.get("codec_type") == "audio"), None)
                        final_duration = float(final_metadata.get("format", {}).get("duration") or 0)
                        expected_duration = sum(float(scene["duration_seconds"]) for scene in plan["scenes"])
                        if not final_video or not final_audio or final_duration <= 0 or output.stat().st_size == 0:
                            raise RuntimeError("O MP4 final não contém vídeo e áudio válidos.")
                        if final_video.get("width") != 720 or final_video.get("height") != 1280:
                            raise RuntimeError("O MP4 final não está no formato vertical esperado de 720×1280.")
                        if abs(final_duration - expected_duration) > 0.75:
                            raise RuntimeError(
                                f"O MP4 final ficou com {final_duration:.1f}s; "
                                f"o storyboard exige {expected_duration:.1f}s."
                            )
                        video_bytes = output.read_bytes()
                        st.session_state["nexus_rendered_video"] = video_bytes
                        st.session_state["nexus_rendered_filename"] = "nexus_video.mp4"
                        st.session_state["nexus_rendered_info"] = {
                            "duration": final_duration,
                            "width": final_video.get("width"),
                            "height": final_video.get("height"),
                            "video_codec": final_video.get("codec_name"),
                            "audio_codec": final_audio.get("codec_name"),
                            "size_mb": len(video_bytes) / (1024 * 1024),
                            "scene_count": len(media),
                            "visual_reviews": [
                                {
                                    "scene": index + 1,
                                    "source": item.get("source", "Stock"),
                                    "confidence": item.get("visual_review_confidence", 0),
                                    "semantic_match": item.get("visual_review_semantic_match", 0),
                                    "style_match": item.get("visual_review_style_match", 0),
                                    "reason": item.get("visual_review_reason", ""),
                                }
                                for index, item in enumerate(media)
                            ],
                            "source_credits": [
                                {
                                    "source": item.get("source", "Stock"),
                                    "title": item.get("source_title", ""),
                                    "url": item.get("source_url", ""),
                                    "author": item.get("author", ""),
                                    "author_url": item.get("author_url", ""),
                                    "license": item.get("license", ""),
                                    "license_url": item.get("license_url", ""),
                                    "credit": item.get("credit", ""),
                                    "attribution_required": item.get("attribution_required", False),
                                }
                                for item in media
                            ],
                        }
                        # Apply the same final-frame audit to the stock-library pipeline.
                        try:
                            from nexus.visual_review import extract_scene_frames, review_scene_frames
                            visual_key = secret("GEMINI_API_KEY")
                            if visual_key:
                                with tempfile.TemporaryDirectory(prefix="nexus_visual_review_") as qa_dir:
                                    frames = extract_scene_frames(output, plan.get("scenes", []), Path(qa_dir))
                                    audit = review_scene_frames(frames, plan.get("scenes", []), visual_key)
                                st.session_state["nexus_rendered_info"]["final_visual_audit"] = audit
                                scores = [item["semantic_score"] for item in audit]
                                st.session_state["nexus_rendered_info"]["final_visual_review_average"] = round(
                                    sum(scores) / max(1, len(scores)), 1
                                )
                            else:
                                st.session_state["nexus_rendered_info"]["final_visual_audit_status"] = "not_configured"
                        except Exception as review_error:
                            st.session_state["nexus_rendered_info"]["final_visual_audit_status"] = "failed"
                            st.warning(f"MP4 validado tecnicamente, mas a auditoria visual final falhou: {review_error}")
                        progress.progress(1.0, text="Vídeo produzido e validado.")
                        st.success("Vídeo MP4 produzido. Áudio, vídeo e integridade do arquivo foram verificados.")
                except Exception as exc:
                    st.error(f"Produção interrompida: {exc}")
                finally:
                    # The MP4 bytes are retained in session_state; temporary source
                    # clips and audio are no longer needed after this run.
                    shutil.rmtree(work, ignore_errors=True)
    
    if st.session_state.get("nexus_rendered_video"):
        info = st.session_state.get("nexus_rendered_info", {})
        st.subheader("Seu vídeo está pronto")
        st.caption(f"{info.get('scene_count', 0)} cenas · {info.get('duration', 0):.1f}s · {info.get('width', 0)}×{info.get('height', 0)} · {info.get('size_mb', 0):.2f} MB")
        if info.get("visual_source"):
            st.caption("Direção visual: " + info["visual_source"])
        if info.get("narration_provider"):
            st.caption("Narração: " + info["narration_provider"])
        editorial_status = (info.get("editorial_pipeline") or {}).get("status")
        if editorial_status == "brain4_validated":
            st.success("Brain 4 executado: edição sincronizada validada.")
        elif editorial_status == "disabled":
            st.caption("Brain 4 não foi executado neste vídeo.")
        if info.get("motion_clip_count"):
            st.caption(
                f"Animação LTX: {info['motion_clip_count']} cenas · "
                f"{info.get('total_i2v_seconds', 0):.1f}s de vídeo gerado · "
                f"{info.get('total_i2v_inference_seconds', 0):.1f}s de inferência GPU "
                "(tempo de inferência, não o total faturado)"
            )
        if info.get("worker_run_id"):
            st.caption(f"[Ver execução do render no GitHub Actions](https://github.com/porraloca42-stack/nexus-video-studio-/actions/runs/{info['worker_run_id']})")
        reviews = info.get("visual_reviews", [])
        if reviews:
            average_confidence = sum(item.get("confidence", 0) for item in reviews) / len(reviews)
            st.caption(f"Revisão visual por IA: {average_confidence:.0f}% de confiança média · {len(reviews)} cenas avaliadas")
            with st.expander("Ver correspondência visual por cena"):
                for item in reviews:
                    st.markdown(f"**Cena {item['scene']} · {item['source']} · {item['confidence']}% de correspondência geral**")
                    st.caption(f"Narração/ação: {item.get('semantic_match', 0)}% · Estilo: {item.get('style_match', 0)}%")
                    st.write(item.get("reason", ""))
        final_audit = info.get("final_visual_audit") or []
        if final_audit:
            st.caption(f"Auditoria visual final Gemini: média {info.get('final_visual_review_average', 0)}/10 · {len(final_audit)} cenas")
            with st.expander("Ver auditoria visual final do MP4"):
                st.dataframe([
                    {"Cena": item["scene_number"], "Aderência": f'{item["semantic_score"]}/10',
                     "Corresponde à fala": "Sim" if item["matches_narration"] else "Revisar",
                     "Problemas": "; ".join(item["issues"]),
                     "Recomendação": item["recommendation"]}
                    for item in final_audit
                ], use_container_width=True, hide_index=True)
        credits = []
        for credit in info.get("source_credits", []):
            provider = credit.get("source", "Stock")
            provider_url = credit.get("url") or {
                "Coverr": "https://coverr.co/",
                "Pixabay": "https://pixabay.com/videos/",
                "Pexels": "https://www.pexels.com/videos/",
                "Wikimedia Commons": "https://commons.wikimedia.org/",
            }.get(provider, "")
            if not provider_url:
                continue
            line = f"[{provider}]({provider_url})"
            if credit.get("author"):
                if credit.get("author_url"):
                    line += f" · [ {credit['author']} ]({credit['author_url']})"
                else:
                    line += f" · {credit['author']}"
            if credit.get("license"):
                license_text = credit["license"]
                if credit.get("license_url"):
                    line += f" · [Licença {license_text}]({credit['license_url']})"
                else:
                    line += f" · Licença {license_text}"
            credits.append(line)
        if credits:
            st.markdown("**Créditos das bibliotecas utilizadas**\n\n" + "\n\n".join(credits))
        st.download_button(
            "Baixar vídeo MP4",
            data=st.session_state["nexus_rendered_video"],
            file_name=st.session_state.get("nexus_rendered_filename", "nexus_video.mp4"),
            mime="video/mp4",
            use_container_width=True,
        )
    

    with st.container(key="nexus-video-stage"):
        if st.session_state.get("nexus_rendered_video"):
            st.video(st.session_state["nexus_rendered_video"])
        else:
            st.markdown("""
            <div class="nexus-preview-stage">
              <svg viewBox="0 0 120 230" role="img" aria-label="Prévia vertical do vídeo">
                <rect x="2" y="2" width="116" height="226" rx="18" fill="none" stroke="#66616f" stroke-width="3"/>
                <path d="M48 84 L48 146 Q48 152 54 148 L82 121 Q87 116 82 111 L54 82 Q48 78 48 84Z" fill="#aaa5b4"/>
              </svg>
              <div class="nexus-preview-caption">SEU VÍDEO GERADO<br/>APARECERÁ AQUI (9:16)</div>
            </div>
            """, unsafe_allow_html=True)


elif active_view == "Biblioteca":
    st.markdown('<div class="nexus-kicker">SEUS PROJETOS</div>', unsafe_allow_html=True)
    st.subheader("Biblioteca")
    if st.session_state.get("nexus_rendered_video"):
        info = st.session_state.get("nexus_rendered_info", {})
        st.markdown("**Último vídeo gerado nesta sessão**")
        st.caption(f"{info.get('duration', 0):.1f}s · {info.get('width', 0)}×{info.get('height', 0)} · {info.get('size_mb', 0):.2f} MB")
        st.video(st.session_state["nexus_rendered_video"])
        st.download_button("Baixar MP4", st.session_state["nexus_rendered_video"], file_name=st.session_state.get("nexus_rendered_filename", "nexus_video.mp4"), mime="video/mp4", use_container_width=True)
    elif st.session_state.get("nexus_plan"):
        plan = st.session_state["nexus_plan"]
        st.info("Há um planejamento nesta sessão, mas o MP4 ainda não foi gerado.")
        st.caption(f"{len(plan.get('scenes', []))} cenas · {sum(float(x.get('duration_seconds', 0) or 0) for x in plan.get('scenes', [])):.0f}s")
        with st.expander("Ver roteiro planejado"):
            for i, scene in enumerate(plan.get("scenes", []), 1):
                st.markdown(f"**Cena {i} · {scene.get('duration_seconds', 0)}s**")
                st.write(scene.get("voiceover", ""))
    else:
        st.info("Os vídeos desta sessão aparecerão aqui. A biblioteca permanente ainda não está implementada.")

elif active_view == "Modelos":
    st.markdown('<div class="nexus-kicker">BIBLIOTECA VISUAL</div>', unsafe_allow_html=True)
    st.subheader("Explore os estilos")
    st.caption("Cada estilo define uma linguagem estética. O conteúdo das cenas continua sendo criado a partir do seu roteiro — nenhum estilo obriga a IA a repetir personagens, objetos ou cenários.")
    for row_start in range(0, len(STYLE_OPTIONS), 2):
        cols = st.columns(2, gap="medium")
        for offset, col in enumerate(cols):
            index = row_start + offset
            if index >= len(STYLE_OPTIONS):
                continue
            option = STYLE_OPTIONS[index]
            profile = STYLE_PROFILES[option]
            with col:
                with st.container(border=True):
                    st.image(style_preview_svg(option), use_container_width=True)
                    st.markdown(f"**{option}**")
                    st.caption(profile["short"])
                    if option == st.session_state.get("nexus_style"):
                        st.caption("Estilo atualmente selecionado")
                    if st.button("Usar este estilo", key=f"library_use_{index}", use_container_width=True, type="primary" if option == st.session_state.get("nexus_style") else "secondary"):
                        st.session_state["nexus_style"] = option
                        st.rerun()

elif active_view == "Perfil":
    st.markdown('<div class="nexus-kicker">CONFIGURAÇÃO</div>', unsafe_allow_html=True)
    st.subheader("Perfil e serviços")
    st.caption("Estado dos serviços. Os valores das chaves nunca são exibidos.")
    st.markdown("**Versão em execução**")
    runtime_sha, runtime_source = get_runtime_build_info()
    if runtime_sha:
        short_sha = runtime_sha[:12]
        st.caption(f"Commit carregado: `{short_sha}` · origem: {runtime_source}")
        st.markdown(
            f"[Abrir este commit no GitHub](https://github.com/porraloca42-stack/nexus-video-studio-/commit/{runtime_sha})"
        )
    else:
        st.warning(
            "Commit em execução não identificado neste ambiente. "
            "Nenhum SHA remoto é usado como substituto."
        )
    with st.expander("Configurações avançadas de produção", expanded=False):
        st.markdown('<div class="nexus-kicker">PRODUÇÃO</div>', unsafe_allow_html=True)
        st.caption(
            "O modo visual é escolhido na tela Criar. O modo econômico evita GPU Modal; "
            "IA original usa créditos Cloudflare e Modal."
        )
        with st.expander("Ferramentas avançadas · diagnóstico das bibliotecas de vídeo"):
            st.caption("Testa busca, licença, download e leitura do vídeo no Wikimedia Commons, Pixabay e Pexels. As chaves nunca são exibidas.")
            if st.button("Testar todas as bibliotecas configuradas", type="secondary"):
                providers = [
                    ("Wikimedia Commons", "", {"wikimedia_enabled": True}),
                    ("Pixabay", secret("PIXABAY_API_KEY"), {"pixabay_key": secret("PIXABAY_API_KEY")}),
                    ("Pexels", secret("PEXELS_API_KEY"), {"pexels_key": secret("PEXELS_API_KEY")}),
                ]
                tested = 0
                with tempfile.TemporaryDirectory(prefix="nexus_library_diagnostics_") as temp_dir:
                    for provider_name, api_key, source_args in providers:
                        if not api_key and provider_name != "Wikimedia Commons":
                            st.warning(f"{provider_name}: chave não configurada nos Secrets.")
                            continue
                        tested += 1
                        try:
                            with st.spinner(f"Testando {provider_name}: autenticação, busca e download..."):
                                results, source_errors = _search_stock_compatible(
                                    "nature landscape",
                                    per_page=5,
                                    relevance_query="nature landscape",
                                    min_relevance=0,
                                    **source_args,
                                )
                                if not results:
                                    detail = "; ".join(source_errors) if source_errors else "A API não retornou clipes relevantes e utilizáveis."
                                    st.error(f"{provider_name}: busca sem resultados — {detail}")
                                    continue
                                chosen = next((item for item in results if item.get("vertical")), results[0])
                                clip_path = download_file(
                                    chosen["url"],
                                    Path(temp_dir) / (provider_name.lower() + "_test.mp4"),
                                )
                                probe = subprocess.run(
                                    [
                                        "ffprobe", "-v", "error",
                                        "-show_entries", "format=duration,size:stream=codec_name,codec_type,width,height",
                                        "-of", "json", str(clip_path),
                                    ],
                                    capture_output=True, text=True, timeout=60,
                                )
                                if probe.returncode != 0:
                                    raise RuntimeError(probe.stderr[-1200:] or "FFprobe não conseguiu ler o arquivo.")
                                metadata = json.loads(probe.stdout)
                                streams = metadata.get("streams", [])
                                video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
                                if not video:
                                    raise RuntimeError("O arquivo baixado não contém uma faixa de vídeo.")
                                duration_seconds = float(metadata.get("format", {}).get("duration") or 0)
                                size_bytes = int(metadata.get("format", {}).get("size") or clip_path.stat().st_size)
                                if duration_seconds <= 0 or size_bytes <= 0:
                                    raise RuntimeError("O MP4 não apresentou duração ou tamanho válidos.")
                                st.success(
                                    f"{provider_name}: busca, {len(results)} candidatos, download e leitura MP4 aprovados."
                                )
                                st.caption(
                                    f"{chosen.get('title') or provider_name} · "
                                    f"{video.get('width')}×{video.get('height')} · "
                                    f"{duration_seconds:.1f}s · {video.get('codec_name', 'codec desconhecido')}"
                                )
                                if source_errors:
                                    st.caption("Avisos de busca: " + " | ".join(source_errors))
                        except Exception as exc:
                            st.error(f"{provider_name}: falha no teste — {exc}")
                if not tested:
                    st.info("Nenhuma biblioteca tem chave configurada. Adicione as chaves nos Secrets e tente novamente.")


    for label, key in [("Direção Gemini", "GEMINI_API_KEY"), ("Narração Fish Audio", "FISH_API_KEY"), ("Render remoto GitHub", "GITHUB_ACTIONS_TOKEN"), ("Geração visual Cloudflare", "CLOUDFLARE_API_TOKEN")]:
        if secret(key):
            st.success(f"{label} · configurado")
        else:
            st.warning(f"{label} · não configurado")
    st.divider()
    st.markdown("**Motor visual**")
    current_mode = st.session_state.get("nexus_render_mode", default_render_mode())
    st.caption(f"Modo selecionado: {current_mode}")
    st.caption(
        "Bibliotecas de vídeo evita GPU Modal e geração Cloudflare. "
        "IA original usa créditos variáveis; custo do vídeo completo ainda não foi validado."
    )
    st.markdown("[Abrir o repositório do NEXUS](https://github.com/porraloca42-stack/nexus-video-studio-)")

