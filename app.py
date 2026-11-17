import base64, json, os, shutil, subprocess, tempfile, inspect, importlib
from pathlib import Path
import requests
import streamlit as st
from nexus.director import create_storyboard, validate_storyboard
from nexus.assets import search_video_sources, download_file, diverse_candidate_shortlist
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

from nexus.visual_styles import STYLE_OPTIONS, STYLE_META, STYLE_PREVIEW_SCENES, STYLE_PROFILES
STYLE_SCENES = [STYLE_PREVIEW_SCENES[name] for name in STYLE_OPTIONS]
def style_preview_svg(style):
    sky, accent, ground, _ = STYLE_META[style]
    scene = STYLE_SCENES[STYLE_OPTIONS.index(style)]
    base = f'<defs><linearGradient id="bg" x2="0" y2="1"><stop stop-color="{sky}"/><stop offset="1" stop-color="{ground}"/></linearGradient><radialGradient id="light"><stop stop-color="{accent}" stop-opacity=".9"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient></defs><rect width="480" height="270" fill="url(#bg)"/>'
    art = {
      "mountain": f'<circle cx="365" cy="75" r="65" fill="url(#light)"/><circle cx="365" cy="75" r="24" fill="{accent}"/><path d="M0 205L95 95 165 180 260 82 380 200 440 125 480 180V270H0Z" fill="{ground}"/>',
      "farmer": f'<circle cx="240" cy="76" r="42" fill="{accent}"/><path d="M130 120Q240 60 350 120L385 145H95Z" fill="#bd9560"/><path d="M180 150Q240 118 300 150L340 270H140Z" fill="#526e56"/><path d="M0 220Q150 180 480 220V270H0Z" fill="{ground}"/>',
      "silhouette": f'<circle cx="350" cy="75" r="70" fill="url(#light)"/><path d="M0 200L120 140 220 205 330 130 480 205V270H0Z" fill="{ground}"/><path d="M205 110Q240 90 265 115L275 175 300 240H180L205 175Z" fill="#080b12"/>',
      "detective": f'<circle cx="240" cy="105" r="46" fill="#b8b8b8"/><path d="M160 85L240 38 320 85Z" fill="#090b10"/><path d="M180 145Q240 115 300 145L360 270H120Z" fill="#10131b"/><path d="M0 230H480" stroke="{accent}" stroke-width="3"/>',
      "watch": f'<path d="M200 15H280L292 75H188Z M188 195H292L280 255H200Z" fill="#a68b5c"/><circle cx="240" cy="135" r="76" fill="#111820" stroke="{accent}" stroke-width="12"/><circle cx="240" cy="135" r="6" fill="{accent}"/><path d="M240 135L240 82M240 135L284 154" stroke="{accent}" stroke-width="5"/>',
      "coffee": f'<circle cx="350" cy="70" r="70" fill="url(#light)"/><path d="M150 130H315L300 215Q230 250 165 215Z" fill="#eee0c9"/><path d="M315 150Q385 135 365 195Q350 220 300 205" fill="none" stroke="#eee0c9" stroke-width="16"/><path d="M210 118Q190 90 215 70M250 118Q230 82 255 58" stroke="#fff" stroke-width="5" fill="none" opacity=".7"/>',
      "waterfall": f'<path d="M0 0H480V100L390 145 310 90 230 150 120 85 0 140Z" fill="{ground}"/><path d="M200 95Q230 140 210 210L190 270H300L270 190Q250 125 280 95Z" fill="#b8e4e8"/><path d="M0 230Q120 190 240 230T480 220V270H0Z" fill="#1c6870"/>',
      "vase": f'<rect x="75" y="0" width="330" height="270" fill="#f0e8d8" opacity=".13"/><path d="M225 65H255L260 110Q315 145 285 225Q240 260 195 225Q165 145 220 110Z" fill="#e0d6c5"/><path d="M240 65Q220 35 190 20M240 65Q270 28 300 15" stroke="#8fa77c" stroke-width="8" fill="none"/>',
      "van": f'<circle cx="370" cy="70" r="60" fill="{accent}"/><path d="M70 150H290L355 190V235H60V185Z" fill="#c18a52"/><circle cx="130" cy="235" r="25" fill="#10151b"/><circle cx="295" cy="235" r="25" fill="#10151b"/><path d="M0 250H480" stroke="#f2d3a0" stroke-width="3"/>',
      "sunset": f'<circle cx="240" cy="120" r="90" fill="{accent}"/><path d="M0 165Q100 120 220 170T480 150V270H0Z" fill="{ground}"/><path d="M0 210H480M0 230H480M0 250H480" stroke="{sky}" stroke-width="6"/>',
      "neon_city": f'<path d="M20 100H105V270H20ZM125 35H220V270H125ZM240 85H330V270H240ZM350 55H460V270H350Z" fill="#11152c" stroke="{accent}" stroke-width="4"/><path d="M40 130H90M145 75H200M260 120H310M375 90H435" stroke="#21d7e8" stroke-width="8"/>',
      "spaceship": f'<circle cx="370" cy="55" r="65" fill="url(#light)"/><path d="M80 150Q240 30 400 150L320 205H160Z" fill="#a9c7d5" stroke="{accent}" stroke-width="6"/><path d="M180 205L140 250M300 205L340 250" stroke="#8cecff" stroke-width="8"/>',
      "castle": f'<path d="M80 220V120H120V80H160V120H200V55H250V120H300V80H340V120H390V220Z" fill="{ground}" stroke="{accent}" stroke-width="5"/><path d="M220 220V160Q240 125 260 160V220" fill="{sky}"/>',
      "surreal": f'<circle cx="240" cy="115" r="85" fill="{accent}" opacity=".75"/><path d="M155 170Q240 65 325 170L300 240H180Z" fill="#d7c6bc"/><circle cx="210" cy="130" r="9" fill="#151823"/><circle cx="270" cy="130" r="9" fill="#151823"/><path d="M210 180Q240 200 270 180" stroke="#151823" stroke-width="6" fill="none"/>',
      "anime_landscape": f'<circle cx="365" cy="70" r="46" fill="{accent}"/><path d="M0 200L100 105 175 180 265 85 380 190 440 120 480 180V270H0Z" fill="{ground}"/><path d="M0 230Q120 200 240 230T480 225" stroke="#e6f4fa" stroke-width="5" fill="none"/>',
      "anime_portrait": f'<circle cx="240" cy="110" r="75" fill="#f1c5a7"/><path d="M155 115Q140 10 245 28Q350 30 320 145L290 95 260 65 200 95Z" fill="#29344e"/><circle cx="210" cy="120" r="9" fill="#202a43"/><circle cx="270" cy="120" r="9" fill="#202a43"/><path d="M170 185Q240 155 310 185L365 270H115Z" fill="#d58f91"/>',
      "editorial": f'<circle cx="335" cy="75" r="65" fill="{accent}"/><path d="M120 245L180 60 260 80 320 245Z" fill="#f0d8b0"/><path d="M165 115Q240 30 300 115" stroke="#273344" stroke-width="16" fill="none"/><path d="M0 250H480" stroke="{ground}" stroke-width="20"/>',
      "lighthouse": f'<path d="M0 210L120 145 230 205 350 135 480 205V270H0Z" fill="{ground}"/><path d="M220 95H270L285 220H205Z" fill="#eee5d0"/><path d="M210 95H280L265 70H225Z" fill="{accent}"/><path d="M0 230Q120 205 240 235T480 225" stroke="#e8f6f5" stroke-width="8" fill="none"/>',
      "comic": f'<path d="M0 0L480 270M480 0L0 270" stroke="{accent}" stroke-width="7"/><path d="M120 270V100L240 30 360 100V270Z" fill="#151a26" stroke="#f0d15c" stroke-width="6"/><circle cx="240" cy="120" r="40" fill="#f0d15c"/>',
      "car": f'<path d="M80 165L130 105H330L390 165L430 205H50Z" fill="#b8d1dd" stroke="{accent}" stroke-width="6"/><circle cx="135" cy="210" r="30" fill="#111820"/><circle cx="350" cy="210" r="30" fill="#111820"/><path d="M150 115H310L350 165H110Z" fill="#18283a"/>',
      "character3d": f'<circle cx="240" cy="95" r="60" fill="#efbf91"/><path d="M180 75Q190 15 250 30Q315 35 300 100L275 70 220 75Z" fill="#493b32"/><circle cx="220" cy="105" r="8" fill="#182333"/><circle cx="265" cy="105" r="8" fill="#182333"/><path d="M150 270Q165 165 240 165Q315 165 330 270Z" fill="{accent}"/>',
      "clay": f'<circle cx="240" cy="120" r="76" fill="#d7a16e" stroke="#805c47" stroke-width="8"/><circle cx="215" cy="110" r="9" fill="#25252b"/><circle cx="265" cy="110" r="9" fill="#25252b"/><path d="M210 150Q240 175 270 150" stroke="#805c47" stroke-width="7" fill="none"/><path d="M160 210Q240 175 320 210L360 270H120Z" fill="{ground}"/>',
      "droplet": f'<path d="M240 35Q110 175 240 230Q370 175 240 35Z" fill="#bceaf0" stroke="{accent}" stroke-width="8"/><circle cx="210" cy="150" r="14" fill="#fff" opacity=".85"/><circle cx="270" cy="180" r="7" fill="#fff" opacity=".7"/>',
      "island": f'<path d="M0 170Q130 130 240 180T480 160V270H0Z" fill="#176e85"/><path d="M80 165Q190 45 340 120Q420 155 395 185Q260 215 80 165Z" fill="#7ea97d"/><path d="M190 125Q240 60 290 125" stroke="#e6d6ae" stroke-width="10" fill="none"/>'
    }
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="480" height="270" viewBox="0 0 480 270">{base}{art[scene]}<rect x="5" y="5" width="470" height="260" rx="13" fill="none" stroke="{accent}" stroke-opacity=".45" stroke-width="3"/></svg>'
    return svg

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root{color-scheme:dark}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:#09090B!important;color:#F4F4F5!important;font-family:'Plus Jakarta Sans',sans-serif!important}
[data-testid="stAppViewContainer"]{background:radial-gradient(circle at 50% 0%,#18122B 0%,#09090B 46%)!important}
[data-testid="stSidebar"],[data-testid="collapsedControl"],[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="manage-app-button"],[data-testid="stFooter"],[data-testid="stBottom"],#MainMenu,header,footer,.stApp>footer,div[class*="viewerBadge"],div[class*="ViewerBadge"],div[class*="viewer-badge"]{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;padding:0!important;margin:0!important;border:0!important}
.block-container{padding-top:2rem!important;padding-bottom:3rem!important;max-width:1280px!important}
.nexus-hero{position:relative;overflow:hidden;padding:1.45rem 1.65rem;border:1px solid #30234d;border-radius:22px;background:linear-gradient(115deg,rgba(24,18,43,.98),rgba(18,18,22,.96) 65%,rgba(30,24,52,.95));box-shadow:0 18px 48px rgba(0,0,0,.38),inset 0 1px 0 rgba(255,255,255,.06);margin-bottom:1rem}
.nexus-brand-lockup{display:flex;align-items:center;justify-content:center;gap:clamp(.65rem,2.8vw,1.15rem);width:100%;min-width:0;margin:0 auto}
.nexus-brand-logo{display:block;width:clamp(64px,18vw,88px);height:clamp(64px,18vw,88px);flex:0 0 auto;object-fit:contain;object-position:center;border-radius:10px;background:#000}
.nexus-brand-copy{display:flex;flex:0 1 auto;min-width:0;flex-direction:column;align-items:flex-start;justify-content:center;line-height:1.05;white-space:nowrap}
.nexus-brand-name{font-size:clamp(1.55rem,6.2vw,2.25rem);font-weight:800;letter-spacing:.10em;color:#f4f4f5;white-space:nowrap}
.nexus-brand-subtitle{font-size:clamp(.78rem,3.2vw,1.08rem);font-weight:650;letter-spacing:.18em;color:#b9a0ff;margin-top:.38rem;white-space:nowrap}
.nexus-kicker{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:#a78bfa;font-weight:800;margin:0 0 .8rem}
.nexus-preview{display:flex;gap:13px;align-items:center;padding:12px;border:1px solid #30234d;border-radius:15px;background:linear-gradient(140deg,rgba(124,58,237,.12),rgba(18,18,22,.7));margin:.4rem 0 .8rem}
.nexus-preview img{width:136px;max-width:42%;aspect-ratio:16/9;object-fit:cover;border-radius:10px}
.nexus-preview-title{font-weight:750;color:#fafafa;margin-bottom:4px}
.nexus-preview-copy{font-size:.8rem;color:#a1a1aa;line-height:1.45}
[data-testid="stVerticalBlockBorderWrapper"]>div{background-color:rgba(18,18,22,.85)!important;backdrop-filter:blur(12px)!important;border:1px solid #27272A!important;border-radius:16px!important;padding:1.1rem!important;box-shadow:0 10px 30px rgba(0,0,0,.3)!important}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stSelectbox"] div[data-baseweb="select"],[data-testid="stMultiSelect"] div[data-baseweb="select"]{background:#18181B!important;border:1px solid #27272A!important;border-radius:10px!important;color:#FAFAFA!important;transition:border-color .2s ease,box-shadow .2s ease!important}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus,[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within{border-color:#8B5CF6!important;box-shadow:0 0 0 1px #8B5CF6!important}
[data-testid="stTextArea"] textarea{line-height:1.6!important;min-height:185px!important}
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
@media(max-width:850px){.block-container{padding:1rem .8rem 7rem!important}.nexus-hero{padding:1rem .7rem;border-radius:17px}.nexus-brand-lockup{gap:.65rem}.nexus-brand-logo{width:clamp(58px,18vw,76px);height:clamp(58px,18vw,76px)}.nexus-brand-name{font-size:clamp(1.45rem,6.4vw,1.9rem);letter-spacing:.08em}.nexus-brand-subtitle{font-size:clamp(.72rem,3.1vw,.92rem);letter-spacing:.15em}.nexus-preview img{width:112px}}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nexus-hero"><div class="nexus-brand-lockup"><img class="nexus-brand-logo" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAAAAAB5Gfe6AAAltElEQVR42u19d5xcVd3+8z33zszWZLPpFdIoIZRQA4YqIAqoFBWEoC+IBUF+r4CvKOIHwVekSHl5xRcsCIgooEgTKaJAQBIDgVQI6XVTtu/szL3nfJ/fH/fO7ibZJFtms0Oy54/d7GZn5pznfHu7QN6WFMC7CPrWrlx9ePetvtXHWH2n7hVI+vD6iJKudPny+q58e4jIR5AO9kSukD2N2fuEXx4h7AXoRTqzK+nyEWRPYYM+9uk0ge2W4mzXR4x2J8qTbQ8lH3XJUBgf4u3GitrrCIxmdxVBhqace47xJdv+omL0nqxpDfb7pNmjz4+PVeSL2T6CytRD0dgC3fgu2ZSPg+4b2sPivZDJIoH95k7bjfX7zs9/8PpPwt9jnTAfhy+6CIk99v59nMuvIbWneu3i40LeuGP+l90YCCP4T94Es6cGYAxwK38Lbw8+/8+5oBJmzz3/b9lwSKQAd/sl7Zi/uI/84h5y/nbv//fkHb1lAEoe/6qL7g+eJF/djYw/6eT5zRPkxrF7qgfgof8MNvLkHQkAKejL7dbuxEPpm0zz6o+CAJT834wB+s9kmr/5iFpA3dy0eDh+ygzW8wVvj/R+xcPnrn+Zac4r3iMtQAPc+vY8rub6Cb0tAHqF/DzgPga0DI/uwPllt5MPPvAgs+p0zqd6MAQk+frTPBfVCHwMf6wmUA15VyfpX3rh2iTv1F+Myb/556xAHTMH9IwFWMg842Fy5Sd+etGHDF2Wt6GiYE8pPZKgFdHPNkzee8ONnkqYnH3EMfPqdjsDZyfK75oN9z95N9VRdfnoSz+ebxtAChoBD7iH7p4fMLSq5Lm3PlYoTmDbIyeH9hQEHvzfsPF/Pv0arbOO37pmQ1khiiuvfEwKMBFpisnn+cvfJOfNfSOr1JC3/i/PKVAvcN+TSjwgYSB+HitxPJS+woxjZh0dHV95iH/o9brD9lcCA3DJ6+cCBig/Mj+bFPHgvcqsc66WStKt4E1+B+kr/yjJloeSrW5q+r17e9dsvmk4Jl8x8bZLupWukUj0GwD+CwyozqYtqWr55F7wkmU9cP4O/r3v+77nma3vV0RQ+lM7FZ+4cxr2nvUYnjqvq+EKib4I4KHsY+ZxBiTV1oZOXcC3rkoJRg7rlYpy9Dt4SBvdLJ7neSaGQgABLr1DhlVAgF/9+f43L+0SDeTI28cJAzH81lP+xawqVR3VWsfMSx8His/tFS0gKJ7++sKH7/uvL3z2pEP3Km1L/cbzPc/zPZSl8Km7+gOYPo+8sgsICDAmAcDDWbO9q9/873cZqlN1jlRnXZb3I4UvntgdGdst7AZ89zsAANdYtblxSX3tupXLN2aDtn9RfNAbVY8vvuhP/7zhZPzXLRB2yjYWDp4y7cdZALh/4dEn/89XhwZJAqCoGNAmFh+U8dzUt4Nestc8h4nfvhQ22fImNZk61q9wK//ROMirWZ3JaMVzEwEAG3590Qj++ZLazvkGnrvuuDnfMfTDU68qPnZ99UTxAIAiVtYMS6o55aVEeHDi30Z7y/Tzgc9kaYMwDG0YhtkmJUmy3pFsbPjd+T+mhoF1WdoVtPwVUp1Shx4eX7W8Ep6PX5HNnL+JzqlTJZ1dG4S8DT5QWbELaX5bv8THtOdIVSXVOXXOWZvN1DsXOmrmpzfRqlM2L8ss/2MQ8HwM6gS/isENN28cAuB8hpbL1+TOr06bNjv+K5XTEb1r8ODTCzdnqdY6jTanjlSnGpLVjs6RIR87ar//pDYefsu4ju9XUP7mfD0Onz12FZ3ytc0MXHR+p5sbMhumIiFI9rKXJuL5mLiYTl9qpFLVOXVWVVWduiaGDY7UgH+Ad1p1yNd+0QnX1cOJJK8d8+IDgTq+s4DWqdI5VWZeZOb78HwMHFoAVm/yppV09gOnVKcu0CCkU3VOqWqbMoHLhmyeNuxxupCdcF2Mj5+xmX/89mq6pmauC6lKks4ps3b5zFHwMPTGZJ7usasyIDlkqIfrmc1aUlXV0dpIHjhV1VAZrsqSIWf6Jz4bMuBcv+Mk0H8DbajhcnJlPamqTsNwXpoavlX1/neRQPJLMybBdIuoo82wy5ErDpvk9k3NTyY9CxAw6jwSEIgIaUBvqLw2y9/YfLt3+0V/WKeTb+koAGVlJ1fSGFl4+QccXa4KEoQMTlJqXnph1CswOO6wZxYYRS83RghQcf7tNwcMnVOGmXSQu/9oWT7wCtfN5i+f/f2Xm9TxjI4xQdF5l6ep1OVP3TM3ki3qVFUZKl9bxWtQhL2fnDGu16NBYhCZJ3fThkpVNltly/ltNsxuetopmbmzmssaGHKOv3OaFRgc9s11dKpLzri7ji2np1pHLuZ8D6l+93GG7PJgQLufJ15S8EPSkWrJoJ5OnTpVZX0dm+5czZA132tyfH5zmObt0a3JTlTACac/zIAN2T8sZNhCTqRTu5F104EB88jv7xICkA6JUcFpG+nUOavBekbHV41oIquOrjbk4oWhrQp4XYcyeWMmv0qrml6+gBqxVPTFhZv5ughuZJaXdR2AvFOOJPB5hk5JVeZMInXqqKtCUrkhzVWsns2s8piO7DtVPIuhsqmO2kaiOGcteTxwK0PnphZSUtzDcQwsSXVWSRsZRU6pdKTLOip5858Yhny7uEM1y28ysMpWalJ16pyG/D1wAQPLuYluX6TJJ6cciYSnICEElRAhRJQWVIWhhOx/NIxvp9zQARIgDDxPQURONAECIvDT3x845meAwwuhX0C9gT4ebn5kLm0rsbrcnZHavFGdknRK1cwbZ+fEwI5ucCZrNkX8H0sBqqoG/NKBn3uUoTI8ovsy0ORJNAhAvPHIf/+65QcATgQCUEj4SULW/3GTUZLe0fePsrENtkMhFX6wvFlERGlyv7SJPy68b58BENc4Y5a4fAPQVYoiAKSrx1TmfiAgvlIg1YvhqG+VG0GpR4qImKDyjp2/Z8kALE4NSRCAbqo2IKmEwfwHpn6xHLAlLxVWXZCHL/x02nkMXcwAOSawls5pusaSa//NgHTOOcsv7YR8BcWr5h5UHfvXLtDQOlV1/OdsuseamG5aWtpZgu3Z5mnFzJlhIySiBgEoRkh6HgQsTgEsH8MEGVkNN5W7nWxfzebLBjgREmoScDAiMLUbDkLmY0WwJQ80dVYEcrsA5CVvg/7NlcuaTA4CxoOzSAJCr4FaOhgkYQRiR+20t69c9r6YhpDoTZIGVLLoHB81peK46ddw3d+16R7rbwlvzWpvTX0u7imSU1sgRMSUqOSiwhQS1xm34yKg/iUeSDJyLAEhISgS6vBSNJf/fHWC3RfheZUi9ZuL+pcAjGggPjmivSOEhwxURIyixiTCY87ljj+diVG+tL2eFihgYORdKLovwvMIAKUGxZpsuQeSzO0a1OIkJK0RScjS22wC38COpUDxe0CsSCNCEkjEQkZYsvxVaHekX09QABKlpQlKiwwUA2tzvKAOTUkvYovgsLo/1jWccMr49mhAct/6jW+JVhFiQBhG5EUSz2/y2B3p1yMApPZpbog3HBPF4hoDQpGhACiDkFT6+OFLP3sGX9t/kprtb3bU4BAkwpicAMI2RTUXJD7Mjz+Xz+IK4cAJ4we0PYNw39iEhwEeHbrvcAFIMc6/9pTqY8959uAFO0iWDQFUDEyu2EyIBBnjq6vh8lGDll8KSOLA6rTEZCsAKEJSBEkIj5tGUggReG7iK7L79+G85fdzF3zJ5iaz1lHLU1TW8lVQkY+g8sOyAvflA+ARCYY5pNMoqwMjaHJDJ7PDp/WdNIaGPEzZ49+Za9njzl8GOGqmwvUK2AUT8X9CWADStiXE346Mz5hig0CigZ+PkKTwEBW3RBziYSPbSfFUmLOAXVc3rlQZhw91c9tiukCdTAozcDiFUfieVHwkAIJ6vfNF4BUsDo+gNrmj3Jqa3o7BLbQybzlq9mCBg6IeCJ2bv2lHH3J8W0K6SJNGDW3pFAyzBWPXFvjY2K5/cb6PIiBfMJQAIjXl+V8nMiO6cPhQRB05jdByDBoqSjEQpYgttrD02paU9XC0YhwNrDioPo/yKDOApEuweeOHLkftzphexiABwG75cpSRICASWO4QiNIRXYIAPVI2FAeJm0kMYPx/1005GIEODWFLBpVtFrDxMSp21i0xpQvJHZ7/iL9tvZ5rlrARCkMHDEUdSI8A0jzofKvFWGMDpusJWotIyC+looIb771pCRp4/Sdt0if+j6vZeNhskFGAxAERHFi/YvJy580nMFxQKUxuH/eMq3IGFMemksvUkMHwghjWYFJEgacUNGROEiQekL4z9xiGtv8NmwMU9/ZfYpECMgYqdIQOcvrntndVCVH0MojxRgKuWtphzvMZPzAz0dWEKTdZAiE7GxEEbVCEAQ1378G8NPrdzWKyD6Y+kLNw+EMBIB1Mi1Ujy75uWBwYfQAtMCPL7+3QkwIgC1ZBKFAiEgSkGJIZodRUSobMlHU/SocaMv/+AL7TFsP+yzzwUJbZFn0enF4OUX15aOPr3AKEA45PhmF8XpSaGCVFJAB5IKyOKstNp9sYUsmhr7x6FXfzC03ZEAlSeIbbWrI82i3srX0xjkj+p9AGTLN5o82A0eHXlugDGM79llTay+Di6luvpciW2sJv2qc0qyH7uiqp2BeKVYcnJr7QJBiogG+FVtCmVYm5+LM22P08nh79xyv5OLUTUTGjMscxLflMJIxL2ESHnulZG/QATFZ0nwmbu5bSltFicfG4XNcjkRCpHAv0BUgFtxjXQXAOa0TVcpq+FlYEXEqtF1ZQnQGI3NQZI0JibkOHBIcHSxn/BxxUXWbA2vxeRB0YsjDwpiCAGGQbAvFuQnoG+6aD+086o1i4BMdDFR3CJlCNNQa8gIgkgHxAhH30SgFDFqj5y0jSqswAPLjIohYzbQeoHxa5cBSDbNwq7xBaTDANQtA9ItRxRINisZW+oBLlKIjOJEgEibzUeqzZ9yfvnWCFhMGAZj1whJEJCG96B1qx9SEHyyys+LGvQ7xeg7XBWbgBQk1n6EVCdTdoF3EOlbI2xbykFAIltZQAHh8ZjDBlzuWm07IVGO4wAw1eIuuinU/u+uSINIzstTZZDppvBvc6YP1wCV8HLqCsGIQa58r1nrxcx83zC6+1j0szVklLNzwtTQK/s70xb3MliC3iDGcQUkE2Lw3LGDAYxaDfQAAB0aNMbtALBqkI/KujqhCAGBTwiKvjJCtWrmfcYSGueECJGoE6CluUBo8MrL93mt0RFRlEWxMJWYTLTMV2/tGyckIChL5+XatgaA6DJHCBJjHZY9nWlV2aBA3nEmPLPymyuS0bFB54wCJswKGd8/hQQuK1lw4xb78SMekRZioSg2fa3/eACDl3eSBdjzpnBRE83oDysACEUoIMBUkjRI2MthorCO1D+bAYGm2ogRYpISYw94iM1bXJRAWlMrAETEcwdegAqEA/z1vScDtkcBe5Wh/xFfK242G+u9yOoBicm+CjbjmbskBESEA7xaD8KKoSoGhDArQgiM7pOdc7htRSBRHLkSgBhqHAwWhFgOTizZiO7HQyS/FNDPQ83G4S6pxsDkFJ1upAD1MD9anYp+404tSxsKnUbVpPBJQKOO4K2GwRICKiSgqBilgkyseg0YWWbRff3F/AIwbiXKK2AMg3WRlUfCmIQIYJCoviw2gIxb6gMkPEBEYaLAAWHswHNKjnItirmsfywuCWMCs2aDp6Y2JNznPIwm81TnZvKjBCFAP8WA0XDE8ImMty70KyCEgfOefthYKiH+XkklARWoGpuWXBbBc1eXXz6oxSROJGPb19RbCd9bVgaD2h/9HXt9vT8Oaexuo5R0FYDtEBYVQ9LIpgEYkpTY7os84SxAfHdt5NubVM7XsaGsqbEASCOqqnLdpPtb9xabFNDiBMsmb6gGMObp1cFbSOBw151wCNucw+RNBg4ctBn1DXEAK84KRUxOrAfVX/MVKCH0ihQAvBL6CVny5ipEtr6IrXZjUydemQsQFtWooYCUhNCZowTQ8Ozj6seEQ4qG731mJQuqZdjglD8DY6tdc7NVl81GfUTKMOtcyO/BBxJ4gFmX6y1S0jmnzKywLmOpdG5zhtrsNo+KcmIY9aGjy8aNF+pqaS0bF2fXpTdOvILrXpmYn8szeQNgfBEwacB3Hvupp/A85kwXI9kQm0GIxWVzklE6KyIRw+YNSI0RaUoDBMo8oIiVv43DyWUjDGAiW0kAmzWCYFxisAz6zBFY9VJ9j3iD0jkx2PpPxQFLgbVXLZy5CQ6eBxVRkiLS3AQLAPTTNzS+IY45FxDZ2oG6NBStLCdFJOGRKsFJP2DOLQxh4swKDBpEOAAwSVw6Fd6dVaYnAGDnxGDLPz2desk6JCYsS9UdGzv6oRMREdHKgWiOAhzek495Gz1G2TJnsyUjPfGXiVDJekrQJAASuHZ/awCQtemWLDOixlsVEbH7TMTspvx4w/liAcXclxySR4//87PTYISghHUSRfKpqMnh9f/q74jju9IIXxXy1GzE7AI0Q8SILb43ZoJkeRQNisyGBKIiCfjMYEU3omA9AYDgqDNXomnjGzhihBqQYHE/jY1XzUUd1K//WcPdnhWIaIUvEOCCUbUeAOkvtnYwVKieO/4seoBkDNDiDGm/fhoX3m6o9VHdjShY1wHYwcAElLzfhMnZJZgCFYAaN9JE/k4mF+OR52tveSVlCSDKomvZoWWEEVD95e9VeRADwS/GW4OyNQ0mCqXGKdZIKTq8sNZf3p2AmHQZAG73B0088xOLaZmqkvMhGnv9kbiPJFjuRf7DfGGDn6v5EGhY6jGuq0u9mUG2LhDJDrkTguz+g5lLCYsBoqAADKb62WK7EwCko8fIlxpUZNfg6Y3wB8Q+bFwQKiQNGnMfmrCDHpl5OoSM8sdikmyZN9V44F61FAf69oxzQ5SKi51KCBAllCACDH05U+x35q52xRIPBgcPxMQGqrq4h5Zxv4A7NJLh4uGgNdcDdzMTlf5r1Aga9RaFZOiiXziuHIUTaNW1NuBFbQekY9USNh9QcAMky8/0cMYI/CeD1g1rfJrwIBiB+MCF/DuSPl6nVccIo6itwqkyXUfdnKFTapaP4RRqBABV1Tmma+mU6mxIbhrVqccudV4Idl7BsE79McCwHO9DhBKsN1SgfjMID7b83oc2TYd1yR9FJY+RkJA4MIRkCaRcAgrp23M/3ZQLGbkomFrUf3UmyqZZ6A69YXYfAHZWrpZ8cQiHX2wRB7UiEwCmQiXKi4m4Yfu++nVMX5MgK5O/EEpsEOWi46TnkZ4fgoQY3DwhDoNJOpYCGJYiYLx3yESyuymxjgvBjn3AIM3ioPo0hkViP9ICygQgRHMGosdfeX8Clz3vhTTrdd3fvOZsfPmtHQYkIaWeEjC6/4+DyJvUsiBKrcEzojLvlovXSzbbpoK6F5Zs83PlxSdg8ZwrD36HobaMeYi8Pss5SR/fXpdOZ26DD0B8nDqXTVnW1mbj5kJVZVM9nWV2HUmlulYZYTORbHRKBrwH/RdzXnHvD1CTLRNM0w8d5j549tQGtnSMRu3O1JBzS3EFad2jZcU5ujv7GZdh1WpqS4cpg2bnlC5r/11HdVZz8t+5MOpGdErrar4NnKT/ylvnZ9eVSVvSE4f5i0bKmMpjy9S0jbqIkETQdMHdCLwPv39KSxH1n94wvhuSbIwaAAhQEykKaJJGXndR/33uM0xsBJAeN1RD/r5mHTzuEtru8OsE+BQXkxrNUci1u5NOQ87+OWm56fh7WrS3wWHPacCadDR1IbIbnEav5vKAkQEQWwF0zkVv2xxwOnyz+O68NU2bbkn/1tfJCExA6bo6iXPhzMl2gdEp31An+NO1s+d7sQ+rZs69f03UlhZH5h1aC4tJ6l6JOJseN4hQjFsjcdVVJaBufR5DWXlaGRyUdg+tBAmY6jrTGnkV0AnM06fb3/itlX3uzf9bJr/M1YrkckRR8tQxlxBu8RlMP5BASjAEduy+YXvPmOxVALTaP1Iee+eAqIA3DJDLjRAiMGKyk4Zd1yaSq2bTxjv7r/yVp3FFKSVXXxWHANBqKUHVK1eAoKAMOBmjt6VV9i4ARf6QEcVVwwwBUIcOdjYbt7bE9RIy/s45bYM4at5cet1ZjzT7FFJNrtlOYusnCn1QGEVBSBoThY+LgFFYkTctaPIkHBOoKMbQ4yNzBo5xKjT39qrJtbduGconZi36yYEPQqHOVAempbIm94ECSpRkhjFxfBHAO4DD4SOs2aUA7DQR2WzHluCgI+MQrhEkiijiLcnGUR2Hm9ZvGcWjqfrr+3jnPi8UT+qCNkDnGKClQI6oyZVVCZYA6eC9vXrfDtiCLCiYBHvC8MjHF6qIVQVGeoz6/xOLfgu35WvUpJteW75xcUKFY8u0VRvkvrZ2UjSXmEhAklDg9c1TmC8TuDsAcIuAyCGAsLUSSH0hWRQ4gFTie2mfW7/GrFy94KZLna+wzOHYCpK09KCat1o6BokKoGZ1KrurLJwOv703J5ojFE0QcY6L6unURc3fGb7W7rQqkRTwzWjmgosnBbUZl6G5EQzZXODA0U0FDpr18UGFwAJbBkQGxdXspEJoPtzotfR8Wg+3o708BpFN+P97R1QcFiMkbWqDJa4nS+QiDMjOqgJc+vVNUhBeYMvycFToIo/FOaeWt9zaEvNi83t8ertIp4YDv8+5kG3HxcQzU+Jfxp6Ry6aPBSbcl79+xw5TQNuG0PaQGeU7qkZlYEqMOQ1RVQsVCxx+uN26gqyOxQ+aPZV2/oItXTItK+lXA/qXkwb2NAts27+wE5KrQK6lQyj+nC/s57zYgkHVyEfe3l57C1ElZR8+lJsFIlsVYENaGhCjamEEIVA2pLy5I1pAugFApzlsH5i49EI9/OLZt/042iOCCX+7fke0U3WsuWZN0sU1BVthLrlhYZHbrAwDQBf/tSkf1ktnheAOAHUYG4WvQCs4df73DVrHJ+z90BJvu5lMmqame+uvxDZFP9HNR28YUweF0lgnqN8Y9NYc2e2tslP/ytCpCzN85vaLJkbDNSNBFvK9HT4I3qDynZ/hrmhgWuvIsPi75Zol0Sgppq06pl8rBgaNKLCsgGDQJ+YzVEs22E+ZMUtoXTxMTtWxatQO9yu4hCcX/Y5q21gAOR3g1OaUQJNzbuO7r0MwZt9eBmDb+zSjq+hCNt00/3T0e4chWwegBXxoC6XV3gPnTlnWD3fGQ/PcFiowziCpklTLDR/ekhSMnFBgz5Qw2P/bDLJcesoZE4AzatTmwsJOlfaInb0+iRvuS36ejlvZgOo0QjL67mgZXCiF+FQ9HzcxzefLB+yNFH5LGye0nKoL+CKKRra5sXaft+gvaf4gN4qWrQDk5jXHQWYqq18r7fQMWOl5U1gwDMU3n9ZQt9zPelOi8k4Cxjoh/oLjP7llb9K2msCeaSc2Chh3UjG2gjUuOW7px99Y7QlMJ6tEmS+wdkAA5W/xQogR8XAqbc51YRhabhqOd8/fWRA3gTP5ajNd7qZjGRDm6KAxG/lZi91MI2Z4ccFI/9hd7T/jw8OiR0j4uIuBy6WzrQa8Eec0HrVTSvNxKxujELjlSsu2OpHKBQ2qVLXkkv6Q8cUFdX54uP1aREO+BaXLWiZAOjZmWHPm1fO1HQC2eSgH/kZaR6Vq/RPraMNcboi5WeXqmOXSCsiQZD4FeLcDIuL2ab4NXhBd5Nl7h7muGLiSJNz105MyuB3fYqsfPdyLVY9fDVWwfIIF1lTF5TEks04MSYFB2Gg4ZTuPVuoKA3v5IATvWRc940BcyYODKYykmcCCpWVeot/ji3Ze1ciBxYN+HeokawyHldGUl0f15gKBTcTOkFdXsvI94SaXNxGWBy1A2aBGAYgYfHGS9WDEgypEEsbL+A39UNSBxIL51xef3i/7m4YECEfTkhokRYoiV4GKDalvgvsm8+XCdQWAdt32aGwE/VFfgYidm+uOFqGRiUWY3IG7UZVr9h084sewSuOR6mIHm+sCyXmGnFgy8WiUJnpTBnD7wgCjzjsqNJCKll4ngSnqqOVGD49eM37O/ySsCCFebniO94+GXFxAwGDQVViWRWGuolNfd2odqa2mgDoX8paOhbAE8xZPxEy6lvKpqD6qIadWnbqQ75eM9gtDC2zzViNO/7BeADgnUX4fEtUB1XRUIl/z1hRcPEdbmB9UmuxCWojE01kwaMAqzZ8Rl1e38oZmUxGKIMwaoVJMwwdRcq9j4QtxePX6ESfMmzLbqERNtQoRFB+uxmXEowqMoKahfWHX+yOWvTFH26gmwjo665Q1i9JUtTy7w+q2uP+0MnydIdVpUEvrlHUvhMowraRVp5YLSwvzebCCr+N3DJgbKa6qzX9rsE6VweQOJ2EFSAB/YeCskustqXx1VSQKqlWplqsG5ROAPA5ROTB5yPlqoolHRihiqx79t6cgajMdVjEUcDy+vDKhAHWwocqG/qMcAJFyygdBCGoh3j8MLhj6O7oozcXNm0gN2dxAZxku7kwu12DyMbiYgdOoWk6DRtrIF7Sc+cRqrh7cqxSwvQSHjrMVn0d6o0cIkUi5zfTTKLNOquZ0av4vvXnHH/LrGQkXNw7DK4aJMgyiR/Svh2/ye3Hdt4MiXE595Ru+e0IhQrjysrqMQX0DmNj4/ijXmWZ/Kh78Di5clwjjLvygIR4uKWKCobp05aZeBWB7BLDv0uSX8fchQx1IMdTKEZoduKY5sfaJgcPCTk07oLdm0yPLT6tLxC2uqXKX6/Vkcq8x42qdybfGkzy8w1RzO/nd9XFFK4NGOs66l00fH/czvuXvOCa47XaeuwGXtT6uqrVrIFNt+V6qINSgbG3EjUwvvvKKlhqBILsi4N9XLTgUOJ//6HgYMxqeiuLL9sFTDFof4BYDYO0avpnX85uuUgK33vj19sF3r4aJnCAm6kIuXOVuezuFOmQ7/hD2KB8mzT9fiVdBUlRyczQIgee9gDR6TAaw6+WGduxXH/z7CWOcRCEc0/SP/j/4av1Vv/YCzE5v7OzbUvxg/+XwfZ/SJi1Nqd20snpYgj2oBrtcbnjt6ms2XhlNB4II3DlL7ilfWgdQqj7IdPr9qLp+wyJjYaLWkvjRZWgw725I7mSGmHQLgC4KBDv8gLub/6MiiHcgrt9Tp5nVy16FE8Cr7jxhqal5/5eNPluq5dYpQPSrPDFZ2X/HV8ZeAMDDBa/olK/DR+T9Zb1XziobOffJQECDpSu7FHFtaPgFVCmAClFGQGB5WrPpRUNoe2agHVr7/vNfqAgjGS4uVXXBqAf2RSK6jbUNXeAsmvTzTz/nWYGKp8yWGRjDSln4q6TrPQC2Nz8DzQ++eMZ52URU5av+Oyet8+54WsLovxvWdkW0qLdy6W3vJ1W9Dc8YNgcCkhaL6HtdYPeetRwEwPOsr6GS1IBVAzFkXO5DPVx1dLs4y84vZ+QnnHMMD/0hM5E9EPB7IxaOLrR4gGAAzmMYOufIZuf4BXijW4w/D6dO7OqOffyENuDD+GeccMzyBjw+rneetb7dTxUMOqJiHTUMnVMNQ14Pb4sLLkp0nUGL3qfV5mnT5gZO6VyW1+Gq/QuMAgTTkz+JnwqvGvCX8GUL23/q8C7v2MdZ2UeU6+ac/Wc6dS7gXfjyJEghIWAwfOrYDK1VqtJyUeWWHG8wbVjXr8zD83c+wSa+fB7TWWXI23D0mAKjgOJL8Cda5xzprLrDtsoBGEwZ0B1493lp/yo28cIZmQZlyDsweFQvAbCdJ0Fg/AFT66xS2fB7ZqORQVuuwalu2Vinjz2ZuvS5w39Bq8oXjzvx+nw+aLTbhZJE7ftHvuc5AKvWITnjv2WbOW+NO5v8tiOWdvLsxpculwcfHflYvUdkJ48rn1BoShCfDOgcXXopN0/siQo+D89yROnD/8rSBfzagNt2tZ2zk5XAXxhSLef8hB9vYYB8bslHv+ofYdhrTjXkt8yh7Vea9QIm0TgDfI6hc87xrBevQKJHPsfHmYtKcC2zanlu+QUFVSgrKJlPq1b5X8fM7bHHIPu46wqUz2OY5TdwmN/NO8vrHybwVYa0ruZF3HNhRwGQzu975G9T+DzDkF9FqpDMAJHi2bSOVfeOOPiCHZ5funVnPo47Cd5sZvkfGC69Q+rboc1vMbTh898Yj/KdnLGb9qs/VvBZBvw+SqSQJEBqEUMuGCI4INHjvXkGb5P/h95NjW2toS8eqQYlxUytdD1coiDw8BpQUUiegMHou+5lhk91DMjuPyd8r/VcNzyvJNC99yJOWvGxptSmq7sVUetElGzFP1ExqJDs4KJ9Zi1sXDWtc32M0mUK8fA5NkwqIDvIx3T+ddMRPWb/bI2PYNC9b+9fOAAIUu9nMnf2jP27HUUw6veH5BcA6YZ48nEJOaN4VwaoBE+csYsIriOb6fch3cd25X4EqapLu/aBkn8t4GH6ePxuhud2HQD0s38t6uJLe+A2ihdy1bBdK5I8fP7GvD4r2HSOYLbcy9n74er12xlw3ENyQTEnWwBFsbEEWMT7u8SP3QKn5PQCsYV9fI0zinphMykUCAH4/+bxnWbHgixz7qI0uoA395gJ9JHAae58vxtm/Ud9+TiNU/Kqjz5iy2DuvXk8f4F2QOxIAnxiYWc1gOxeBPD8mbuOAQoPOg+ffmwXOsEFyA3ec9sZ7/6Ro/MueZYep69/ynfY41br87kmle7eNk4HjiA9w1sd+yPp5fMP6GhY7iNw212KZozY0EGXnLuAPnpB25aM2f1N/R2ucu8js9UeuSjj7dHH7yUOlT0P385sY88WSQVEBtI7VCMfPaR2F0O2D/Pd1NnpW33E3Adm3432rT5q7tt1H3p7BBym7453rzvvw6+PivsO0bf6KKEPzL7Vtzq8/j+ZzCF8sOUwqAAAAABJRU5ErkJggg==" alt="Logo NEXUS"><div class="nexus-brand-copy"><div class="nexus-brand-name">NEXUS</div><div class="nexus-brand-subtitle">VIDEO STUDIO</div></div></div></div>', unsafe_allow_html=True)
st.caption("Versão: NEXUS-2026.11.17-style-grammar-and-library-2")


# Main production workspace and a separate style reference library.
tab_create, tab_styles = st.tabs(["Criar", "Estilos"])

with tab_create:
    if "nexus_style" not in st.session_state or st.session_state["nexus_style"] not in STYLE_OPTIONS:
        st.session_state["nexus_style"] = "Cinematográfico"
    
    col_editor, col_preview = st.columns([1.5, 1], gap="large")
    
    with col_editor:
        with st.container(border=True):
            st.markdown('<div class="nexus-kicker">01 · Conteúdo</div>', unsafe_allow_html=True)
            topic = st.text_area("Assunto ou roteiro", height=145, placeholder="Cole seu roteiro completo ou descreva o vídeo que deseja criar.")
            duration = st.selectbox("Duração do vídeo", [40, 50, 60], index=1, format_func=lambda value: f"{value} segundos")
        with st.container(border=True):
            st.markdown('<div class="nexus-kicker">Produção</div>', unsafe_allow_html=True)
            render_mode = st.selectbox(
                "Motor de produção visual",
                ["Imagens originais · Cloudflare + Modal I2V + Remotion", "Bibliotecas de vídeo (alternativo)"],
                index=0,
                help="Fluxo principal: Cloudflare gera o keyframe de cada cena, Modal/LTX-Video anima cada keyframe em um clipe MP4 e Remotion monta o vídeo final. Requer MODAL_TOKEN_ID e MODAL_TOKEN_SECRET nos GitHub Actions Secrets e o worker Modal implantado. Bibliotecas de vídeo permanecem como alternativa.",
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
    
    with col_preview:
        with st.container(border=True):
            st.markdown('<div class="nexus-kicker">02 · Direção visual</div>', unsafe_allow_html=True)
            style = st.session_state["nexus_style"]
            preview_svg = style_preview_svg(style)
            preview_b64 = base64.b64encode(preview_svg.encode("utf-8")).decode("ascii")
            preview_copy = STYLE_META[style][3]
            st.markdown(
                f'<div class="nexus-preview"><img src="data:image/svg+xml;base64,{preview_b64}" alt="Referência visual {style}"><div><div class="nexus-preview-title">{style}</div><div class="nexus-preview-copy">{preview_copy}</div></div></div>',
                unsafe_allow_html=True
            )
            with st.expander("Escolher estilo visual · 18 estilos", expanded=False):
                st.caption("Referências visuais simplificadas · toque para selecionar.")
                with st.container(key="nexus-style-gallery"):
                    for row_start in range(0, len(STYLE_OPTIONS), 2):
                        cols = st.columns(2)
                        for offset, col in enumerate(cols):
                            index = row_start + offset
                            if index >= len(STYLE_OPTIONS):
                                continue
                            option = STYLE_OPTIONS[index]
                            with col:
                                is_selected = option == st.session_state["nexus_style"]
                                st.image(style_preview_svg(option), width=85)
                                if st.button(("✓ " if is_selected else "") + option, key="style_" + str(index), type="primary" if is_selected else "secondary", use_container_width=True):
                                    st.session_state["nexus_style"] = option
                                    st.rerun()
            style = st.session_state["nexus_style"]
        with st.container(border=True):
            st.markdown('<div class="nexus-kicker">Narração</div>', unsafe_allow_html=True)
            fish_api_key = secret("FISH_API_KEY")
            if "nexus_fish_voice_id" not in st.session_state:
                st.session_state["nexus_fish_voice_id"] = secret("FISH_VOICE_ID")
            if "nexus_fish_voice_name" not in st.session_state:
                st.session_state["nexus_fish_voice_name"] = ""
    
            if not fish_api_key:
                st.warning("Configure FISH_API_KEY nos Secrets do Streamlit para carregar as vozes.")
            else:
                selected_name = st.session_state.get("nexus_fish_voice_name") or "Nenhuma voz selecionada"
                st.markdown("**NARRAÇÃO**")
                st.text(selected_name)
                st.caption("40 modelos selecionados manualmente · IDs preservados por categoria")
                with st.expander("🎙️ Escolher voz", expanded=False):
                    st.caption("As categorias seguem sua lista. A separação masculino/feminino é feita somente quando os metadados identificam o gênero; os demais ficam em Não identificado.")
                    catalog_key = "nexus_curated_voice_catalog_v1"
                    if catalog_key not in st.session_state:
                        try:
                            with st.spinner("Consultando os metadados das 40 vozes selecionadas..."):
                                st.session_state[catalog_key] = fish_audio.list_curated_voice_catalog(
                                    fish_api_key, max_workers=8
                                )
                        except Exception as catalog_error:
                            st.session_state[catalog_key] = {"error": str(catalog_error)}
                    narrator_catalog = st.session_state[catalog_key]
                    if isinstance(narrator_catalog, dict) and narrator_catalog.get("error"):
                        st.error(f"Não foi possível carregar o catálogo: {narrator_catalog['error']}")
                        if st.button("Tentar novamente", key="retry_curated_voices"):
                            st.session_state.pop(catalog_key, None)
                            st.rerun()
                    else:
                        gender_groups = (
                            ("male", "Masculinas"),
                            ("female", "Femininas"),
                            ("unknown", "Gênero não identificado"),
                        )
                        for category in ("CapCut", "ElevenLabs", "Licenciadas Fish"):
                            category_voices = narrator_catalog.get(category, [])
                            with st.expander(f"{category} · {len(category_voices)} modelos", expanded=False):
                                for gender, gender_label in gender_groups:
                                    voices = [item for item in category_voices if item.get("gender") == gender]
                                    st.markdown(f"**{gender_label} · {len(voices)}**")
                                    if not voices:
                                        st.caption("Nenhuma voz identificada nesta divisão.")
                                    for voice_option in voices:
                                        voice_col, sample_col = st.columns([1.1, 1.5], vertical_alignment="center")
                                        with voice_col:
                                            is_selected = voice_option["id"] == st.session_state.get("nexus_fish_voice_id", "")
                                            st.markdown(f"**{voice_option['title']}**")
                                            st.caption(f"ID: {voice_option['id']}")
                                            details = []
                                            source_label = str(voice_option.get("source") or "").casefold()
                                            if "pvc" in source_label:
                                                details.append("Professional Voice Clone")
                                            if voice_option.get("licensed"):
                                                details.append("Licenciada pela Fish Audio")
                                            if voice_option.get("author"):
                                                details.append(voice_option["author"])
                                            if details:
                                                st.caption(" · ".join(details))
                                            if voice_option.get("description"):
                                                st.caption(voice_option["description"][:150])
                                            if not voice_option.get("metadata_available"):
                                                st.caption("Metadados indisponíveis; ID mantido conforme sua lista.")
                                            if st.button(
                                                "Selecionada" if is_selected else "Usar esta voz",
                                                key=f"curated_voice_pick_{voice_option['id']}",
                                                use_container_width=True,
                                                type="primary" if is_selected else "secondary",
                                            ):
                                                st.session_state["nexus_fish_voice_id"] = voice_option["id"]
                                                st.session_state["nexus_fish_voice_name"] = f"{category} · {voice_option['title']}"
                                                st.rerun()
                                        with sample_col:
                                            if voice_option.get("sample_audio"):
                                                st.audio(voice_option["sample_audio"], format="audio/mp3")
                                            else:
                                                st.caption("Amostra não publicada ou indisponível.")
            voice = st.session_state.get("nexus_fish_voice_id", "")
    
    if st.button("Planejar vídeo", type="primary", use_container_width=True):
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
                f"Escrevendo o roteiro para {duration}s, criando as cenas e ajustando a linha do tempo..."
            ):
                try:
                    plan = create_storyboard(topic, style, duration, secret)
                    errors = validate_storyboard(plan, duration)
                    actual_duration = sum(
                        float(scene.get("duration_seconds", 0) or 0)
                        for scene in plan.get("scenes", [])
                    )
                    if abs(actual_duration - float(duration)) > 0.001:
                        errors.append(
                            f"Falha interna de duração: foram atribuídos {actual_duration:.1f}s "
                            f"para uma solicitação de {duration}s."
                        )
                    if errors:
                        raise RuntimeError(
                            "O diretor não entregou um roteiro válido: " + " ".join(errors)
                        )
                    st.session_state["nexus_plan"] = plan
                    st.session_state["nexus_errors"] = []
                    st.success(
                        f"Roteiro criado: {len(plan['scenes'])} cenas · "
                        f"{actual_duration:.0f}s, conforme solicitado."
                    )
                except Exception as exc:
                    st.error(str(exc))
    
    if "nexus_plan" in st.session_state:
        plan = st.session_state["nexus_plan"]
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
    
        if st.button("Produzir vídeo completo", type="primary", use_container_width=True):
            coverr_key = ""
            pixabay_key = secret("PIXABAY_API_KEY")
            pexels_key = secret("PEXELS_API_KEY")
            configured_libraries = [
                name for name, key in (
                    ("Wikimedia Commons", True), ("Pixabay", pixabay_key), ("Pexels", pexels_key)
                ) if key
            ]
            if render_mode == "Bibliotecas de vídeo (alternativo)" and len(configured_libraries) == 1:
                st.warning(
                    f"Somente {configured_libraries[0]} está configurada. "
                    "O NEXUS fará revisão visual dos clipes, mas a variedade de bibliotecas "
                    "depende de configurar outras fontes."
                )
            if st.session_state.get("nexus_errors"):
                st.error("O storyboard precisa ser corrigido antes da produção.")
            elif render_mode == "Imagens originais · Cloudflare + Modal I2V + Remotion":
                github_token = secret("GITHUB_ACTIONS_TOKEN")
                cloudflare_token = secret("CLOUDFLARE_API_TOKEN")
                if not github_token or not cloudflare_token or not fish_api_key or not voice:
                    st.error("Configure GITHUB_ACTIONS_TOKEN, CLOUDFLARE_API_TOKEN e FISH_API_KEY, e selecione uma voz da biblioteca Fish Audio.")
                    st.info("O repositório GitHub também precisa dos Secrets CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, MODAL_TOKEN_ID e MODAL_TOKEN_SECRET. O worker Modal deve estar implantado. O manifesto e o MP4 trafegam criptografados.")
                else:
                    progress = st.progress(0.05, text="Enviando storyboard para o trabalhador audiovisual...")
                    try:
                        from nexus.github_renderer import render_on_github
                        def update_worker_progress(message):
                            progress.progress(0.55, text=message)
                        result = render_on_github(
                            plan, voice, github_token, encryption_secret=cloudflare_token,
                            fish_api_key=fish_api_key,
                            fish_voice_id=voice,
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
                            "size_mb": len(video_bytes) / (1024 * 1024),
                            "scene_count": len(plan.get("scenes", [])),
                            "motion_clip_count": len(report.get("motion_clips") or []),
                            "total_i2v_seconds": float(report.get("total_i2v_seconds") or 0),
                            "total_i2v_inference_seconds": float(report.get("total_i2v_inference_seconds") or 0),
                            "visual_source": report.get("visual_source", "Cloudflare + Modal I2V + Remotion"),
                            "worker_run_id": result.get("run_id"),
                            "visual_reviews": [],
                            "source_credits": [],
                        }
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
                                scored = [item["semantic_score"] for item in reviews]
                                average = round(sum(scored) / max(1, len(scored)), 1)
                                st.session_state["nexus_rendered_info"]["final_visual_review_average"] = average
                                st.session_state["nexus_rendered_info"]["visual_review_status"] = (
                                    "needs_attention" if any(not item["matches_narration"] or item["semantic_score"] < 6 for item in reviews)
                                    else "reviewed"
                                )
                                st.caption(f"Auditoria visual Gemini: média semântica {average}/10 em {len(reviews)} cenas.")
                                with st.expander("Auditoria visual por cena"):
                                    st.dataframe([
                                        {"Cena": item["scene_number"], "Aderência": f'{item["semantic_score"]}/10',
                                         "Corresponde à fala": "Sim" if item["matches_narration"] else "Revisar",
                                         "Problemas": "; ".join(item["issues"]),
                                         "Recomendação": item["recommendation"]}
                                        for item in reviews
                                    ], use_container_width=True, hide_index=True)
                            else:
                                st.session_state["nexus_rendered_info"]["visual_review_status"] = "not_configured"
                                st.warning("MP4 validado tecnicamente; auditoria visual não executada porque GEMINI_API_KEY não está disponível neste ambiente.")
                        except Exception as review_error:
                            st.session_state["nexus_rendered_info"]["visual_review_status"] = "failed"
                            st.warning(f"MP4 produzido, mas a auditoria visual não pôde ser concluída: {review_error}")
                        progress.progress(1.0, text="Render e verificações concluídos.")
                        st.success("Vídeo MP4 produzido. O trabalhador verificou vídeo, áudio, resolução e duração.")
                    except Exception as exc:
                        progress.empty()
                        st.error(f"Produção Cloudflare + Remotion interrompida: {exc}")
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
        st.video(st.session_state["nexus_rendered_video"])
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
    

with tab_styles:
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
