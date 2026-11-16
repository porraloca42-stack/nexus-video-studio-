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


st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{color-scheme:dark;--nx-bg:#080d13;--nx-panel:#101923;--nx-panel2:#131f2b;--nx-line:#253747;--nx-text:#edf4f8;--nx-muted:#91a4b3;--nx-cyan:#49d7e8;--nx-blue:#3887ff}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:#080d13!important;color:var(--nx-text)!important;font-family:'DM Sans',sans-serif!important}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 65% -15%,rgba(29,105,135,.22),transparent 42%),radial-gradient(ellipse at 0% 40%,rgba(36,77,123,.12),transparent 35%),#080d13!important}
[data-testid="stSidebar"],[data-testid="collapsedControl"],[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="manage-app-button"],#MainMenu,header,footer{display:none!important;visibility:hidden!important}
.block-container{max-width:1440px!important;padding:1.65rem 2.3rem 4rem!important}
.nexus-hero{position:relative!important;overflow:hidden!important;display:flex!important;align-items:flex-end!important;justify-content:space-between!important;gap:2rem!important;padding:2rem 2.15rem!important;margin:0 0 1.2rem!important;border:1px solid #284252!important;border-radius:22px!important;background:linear-gradient(112deg,#122330 0%,#101923 55%,#102a36 100%)!important;box-shadow:0 24px 65px rgba(0,0,0,.34),inset 0 1px rgba(255,255,255,.04)!important}
.nexus-hero:before{content:""!important;position:absolute!important;width:390px!important;height:390px!important;right:7%!important;top:-290px!important;border-radius:50%!important;background:rgba(73,215,232,.2)!important;filter:blur(20px)!important;pointer-events:none!important}
.nexus-hero:after{content:"N"!important;position:absolute!important;right:7%!important;bottom:-100px!important;font:700 19rem/1 'Space Grotesk',sans-serif!important;color:rgba(73,215,232,.035)!important;pointer-events:none!important}
.nexus-brand{position:relative!important;z-index:1!important;font:700 clamp(2rem,4vw,3.15rem)/1.02 'Space Grotesk',sans-serif!important;letter-spacing:-.065em!important;color:#f4fbff!important}
.nexus-brand:after{content:" / VIDEO STUDIO"!important;color:var(--nx-cyan)!important;font-size:.48em!important;letter-spacing:.015em!important;white-space:nowrap!important}
.nexus-tagline{position:relative!important;z-index:1!important;max-width:650px!important;font-size:.96rem!important;line-height:1.6!important;color:#a9bdca!important;margin-top:.8rem!important}
.nexus-hero .nexus-kicker{color:var(--nx-cyan)!important}
.nx-hero-side{position:relative!important;z-index:2!important;min-width:180px!important;text-align:right!important}
.nx-live{display:inline-flex!important;align-items:center!important;gap:8px!important;padding:9px 13px!important;border:1px solid rgba(73,215,232,.25)!important;border-radius:999px!important;background:rgba(7,17,25,.45)!important;color:#c6f7fa!important;font-size:.72rem!important;font-weight:700!important;letter-spacing:.12em!important;text-transform:uppercase!important}
.nx-live:before{content:""!important;width:7px!important;height:7px!important;border-radius:50%!important;background:#48d9a2!important;box-shadow:0 0 12px #48d9a2!important}
.nx-workflow{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:10px!important;margin:0 0 1.35rem!important}
.nx-step{display:flex!important;align-items:center!important;gap:12px!important;padding:13px 16px!important;border:1px solid #223746!important;border-radius:14px!important;background:linear-gradient(120deg,rgba(17,29,40,.95),rgba(13,22,31,.95))!important}
.nx-step-num{display:grid!important;place-items:center!important;flex:0 0 30px!important;width:30px!important;height:30px!important;border:1px solid rgba(73,215,232,.32)!important;border-radius:9px!important;background:rgba(73,215,232,.09)!important;color:var(--nx-cyan)!important;font:700 .78rem 'Space Grotesk',sans-serif!important}
.nx-step-title{font-size:.82rem!important;font-weight:700!important;color:#eaf5f8!important}
.nx-step-sub{font-size:.68rem!important;color:#8198a8!important;margin-top:2px!important}
.nexus-kicker,.nx-section-title{font:700 .69rem 'DM Sans',sans-serif!important;letter-spacing:.15em!important;text-transform:uppercase!important;color:var(--nx-cyan)!important;margin:0 0 .9rem!important}
.nexus-preview{display:flex!important;gap:15px!important;align-items:center!important;padding:14px!important;border:1px solid #2a4556!important;border-radius:15px!important;background:linear-gradient(125deg,rgba(27,66,83,.42),rgba(14,25,35,.85))!important;margin:.45rem 0 1rem!important}
.nexus-preview img{width:150px!important;max-width:42%!important;aspect-ratio:16/9!important;object-fit:cover!important;border-radius:10px!important;border:1px solid #385568!important}
.nexus-preview-title{font:700 1rem 'Space Grotesk',sans-serif!important;color:#f2fbff!important;margin-bottom:5px!important}
.nexus-preview-copy{font-size:.8rem!important;color:#9bb0bd!important;line-height:1.5!important}
[data-testid="stVerticalBlockBorderWrapper"]>div{background:linear-gradient(145deg,rgba(18,30,42,.98),rgba(13,22,31,.98))!important;border:1px solid #263b4b!important;border-radius:18px!important;padding:1.25rem!important;box-shadow:0 14px 34px rgba(0,0,0,.24),inset 0 1px rgba(255,255,255,.025)!important}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stSelectbox"] div[data-baseweb="select"],[data-testid="stMultiSelect"] div[data-baseweb="select"]{background:#0b141d!important;border:1px solid #2a4050!important;border-radius:11px!important;color:#edf7fb!important;box-shadow:none!important;transition:border-color .18s ease,box-shadow .18s ease!important}
[data-testid="stTextInput"] input:focus,[data-testid="stTextArea"] textarea:focus,[data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within,[data-testid="stMultiSelect"] div[data-baseweb="select"]:focus-within{border-color:var(--nx-cyan)!important;box-shadow:0 0 0 1px rgba(73,215,232,.42)!important}
[data-testid="stTextArea"] textarea{line-height:1.65!important;min-height:195px!important;padding:1rem!important}
[data-testid="stWidgetLabel"] p,label,[data-testid="stMarkdownContainer"] strong{color:#e7f0f5!important}
[data-testid="stCaptionContainer"],.stCaption{color:#91a4b3!important}
div[data-testid="stButton"] button,div[data-testid="stDownloadButton"] button{background:#172632!important;color:#dcebf1!important;border:1px solid #30495a!important;border-radius:11px!important;min-height:2.8rem!important;font-weight:700!important;box-shadow:none!important;transition:all .18s ease!important}
div[data-testid="stButton"] button:hover,div[data-testid="stDownloadButton"] button:hover{border-color:var(--nx-cyan)!important;color:#fff!important;transform:translateY(-1px)!important}
div[data-testid="stButton"] button[kind="primary"],div[data-testid="stDownloadButton"] button[kind="primary"]{background:linear-gradient(105deg,#147e9a,#2775cb)!important;color:white!important;border:1px solid #42bcd0!important;border-radius:12px!important;font-weight:800!important;box-shadow:0 8px 22px rgba(17,128,165,.23)!important}
div[data-testid="stButton"] button[kind="primary"]:hover{box-shadow:0 10px 28px rgba(17,160,190,.32)!important}
[data-testid="stExpander"]{border:1px solid #263d4d!important;border-radius:14px!important;background:rgba(13,24,34,.85)!important;overflow:hidden!important}
[data-testid="stExpander"] summary{color:#e7f0f5!important;font-weight:700!important;padding:.85rem 1rem!important}
[data-testid="stAudio"]{border-radius:12px!important;overflow:hidden!important}
[data-testid="stVideo"]{max-width:340px!important;margin:0 auto!important;border-radius:18px!important;overflow:hidden!important;border:1px solid #345265!important;box-shadow:0 18px 45px rgba(0,0,0,.55)!important}
[data-testid="stAlert"]{border-radius:13px!important;border:1px solid #2c4656!important}
[data-testid="stProgress"]>div>div{background:linear-gradient(90deg,#147e9a,#49d7e8)!important}
[data-testid="stMetric"]{padding:.85rem!important;border:1px solid #263d4d!important;border-radius:13px!important;background:rgba(11,21,30,.75)!important}
[data-testid="stMetricLabel"]{color:#91a4b3!important}
div.st-key-nexus-style-gallery div[data-testid="stHorizontalBlock"]{gap:.8rem!important}
div.st-key-nexus-style-gallery div[data-testid="stImage"] img{border-radius:10px!important;border:1px solid #2b4657!important}
hr{border-color:#243847!important}
@media(max-width:850px){
.block-container{padding:1rem .8rem 3rem!important}
.nexus-hero{display:block!important;padding:1.35rem!important;border-radius:17px!important}
.nexus-brand{font-size:2rem!important}
.nx-hero-side{margin-top:1rem!important;text-align:left!important}
.nx-workflow{gap:6px!important}
.nx-step{padding:10px 8px!important;gap:7px!important}
.nx-step-num{width:25px!important;height:25px!important;flex-basis:25px!important}
.nx-step-title{font-size:.7rem!important}
.nx-step-sub{font-size:.61rem!important}
[data-testid="stHorizontalBlock"]{gap:.65rem!important}
[data-testid="stVerticalBlockBorderWrapper"]>div{padding:.9rem!important}
.nexus-preview img{width:112px!important}
}
@media(max-width:600px){.nx-workflow{grid-template-columns:1fr!important}.nx-step{padding:9px 12px!important}.nx-step-sub{font-size:.68rem!important}.nexus-brand{font-size:1.7rem!important}}
</style>
""", unsafe_allow_html=True)



STYLE_OPTIONS = [
    "Cinematográfico realista", "Documentário cinematográfico",
    "Dark cinematográfico", "Filme noir", "Publicidade premium",
    "Lifestyle realista", "Natureza documental", "Minimalista clean",
    "Vintage filme 35mm", "VHS retrô", "Cyberpunk neon",
    "Ficção científica futurista", "Fantasia cinematográfica",
    "Surrealismo fotográfico", "Anime 2D", "Anime 3D",
    "Ilustração editorial", "Aquarela artística", "Graphic novel",
    "3D realista", "3D estilizado", "Stop motion",
    "Macro e detalhes", "Drone e paisagens aéreas"
]
STYLE_META = {
    "Cinematográfico realista": ("#182638","#d59b58","#526b78","Luz natural, profundidade e contraste de cinema."),
    "Documentário cinematográfico": ("#263b35","#d4bd83","#758b71","Textura natural e sensação observacional."),
    "Dark cinematográfico": ("#101522","#8b76a8","#30384f","Sombras profundas e luz recortada."),
    "Filme noir": ("#101319","#d6d1c5","#454b56","Preto e branco, sombras dramáticas."),
    "Publicidade premium": ("#26364b","#f0c77b","#8a9da8","Acabamento elegante e luz controlada."),
    "Lifestyle realista": ("#b5c7c6","#f2c78d","#647f75","Cenas cotidianas, acolhedoras e naturais."),
    "Natureza documental": ("#193b35","#e6c77b","#668d62","Verdes orgânicos e luz ambiente."),
    "Minimalista clean": ("#dce5e8","#f2c987","#9bb1b8","Poucos elementos e espaço visual."),
    "Vintage filme 35mm": ("#493a32","#d6a46c","#8d7254","Grão suave e tons analógicos quentes."),
    "VHS retrô": ("#25234b","#f0789b","#3c8292","Cores deslocadas e estética de fita."),
    "Cyberpunk neon": ("#171a3b","#ff4fa3","#16c8d2","Neon magenta e ciano em alto contraste."),
    "Ficção científica futurista": ("#132b43","#78d8e8","#5274a5","Luz tecnológica e atmosfera futurista."),
    "Fantasia cinematográfica": ("#29264c","#f0c16e","#78689d","Luz mágica e atmosfera épica."),
    "Surrealismo fotográfico": ("#39405b","#e9a6b1","#8b9d9a","Composições oníricas com aparência fotográfica."),
    "Anime 2D": ("#7ab8d5","#ffdc83","#e28d83","Cores ilustradas e contornos expressivos."),
    "Anime 3D": ("#526b9a","#f6c77c","#9a8ac2","Personagens e cenários estilizados em volume."),
    "Ilustração editorial": ("#e4d6b9","#d78b63","#63818a","Formas gráficas e paleta editorial."),
    "Aquarela artística": ("#c4d9d2","#edc58e","#8aaeb1","Pigmentos suaves e bordas orgânicas."),
    "Graphic novel": ("#252b38","#e5b44f","#a94d50","Contraste forte, blocos de cor e traço marcado."),
    "3D realista": ("#29465b","#f2c67b","#7294a0","Materiais, volume e iluminação realistas."),
    "3D estilizado": ("#546c9b","#ffd27b","#9c83c5","Formas tridimensionais com cores estilizadas."),
    "Stop motion": ("#6e5142","#e6bd78","#8b9b72","Textura artesanal e sensação de miniatura."),
    "Macro e detalhes": ("#183c43","#e6b96d","#6b9b91","Enquadramentos próximos e foco seletivo."),
    "Drone e paisagens aéreas": ("#39728a","#f2cb83","#6e9d83","Escala ampla e perspectiva aérea.")
}
STYLE_SCENES = [
    "mountain", "farmer", "silhouette", "detective", "watch", "coffee",
    "waterfall", "vase", "van", "sunset", "neon_city", "spaceship",
    "castle", "surreal", "anime_landscape", "anime_portrait", "editorial",
    "lighthouse", "comic", "car", "character3d", "clay", "droplet", "island"
]
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
[data-testid="stSidebar"],[data-testid="collapsedControl"],[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="manage-app-button"],#MainMenu,header,footer{display:none!important;visibility:hidden!important}
.block-container{padding-top:2rem!important;padding-bottom:3rem!important;max-width:1280px!important}
.nexus-hero{position:relative;overflow:hidden;padding:1.45rem 1.65rem;border:1px solid #30234d;border-radius:22px;background:linear-gradient(115deg,rgba(24,18,43,.98),rgba(18,18,22,.96) 65%,rgba(30,24,52,.95));box-shadow:0 18px 48px rgba(0,0,0,.38),inset 0 1px 0 rgba(255,255,255,.06);margin-bottom:1rem}
.nexus-brand{font-size:clamp(1.35rem,3vw,2rem);font-weight:800;letter-spacing:.12em;color:#f4f4f5}
.nexus-tagline{font-size:.92rem;color:#a1a1aa;margin-top:.35rem}
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
@media(max-width:850px){.block-container{padding:1rem .8rem 2.5rem!important}.nexus-hero{padding:1.1rem;border-radius:17px}.nexus-preview img{width:112px}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="nexus-hero">
  <div>
    <div class="nexus-kicker">AI CREATIVE PRODUCTION SYSTEM · WORKSPACE</div>
    <div class="nexus-brand">NEXUS</div>
    <div class="nexus-tagline">Um estúdio de produção audiovisual. Do conceito à direção, da narração à renderização final.</div>
  </div>
  <div class="nx-hero-side"><span class="nx-live">Studio online</span></div>
</div>
<div class="nx-workflow">
  <div class="nx-step"><span class="nx-step-num">01</span><div><div class="nx-step-title">Briefing & roteiro</div><div class="nx-step-sub">Defina o conteúdo e a duração</div></div></div>
  <div class="nx-step"><span class="nx-step-num">02</span><div><div class="nx-step-title">Direção visual</div><div class="nx-step-sub">Escolha a linguagem cinematográfica</div></div></div>
  <div class="nx-step"><span class="nx-step-num">03</span><div><div class="nx-step-title">Voz & produção</div><div class="nx-step-sub">Configure a narração e o motor</div></div></div>
</div>
""", unsafe_allow_html=True)
st.caption("NEXUS VIDEO STUDIO · WORKSPACE PREVIEW")

if "nexus_style" not in st.session_state or st.session_state["nexus_style"] not in STYLE_OPTIONS:
    st.session_state["nexus_style"] = "Cinematográfico realista"

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
        with st.expander("Escolher estilo visual · 24 referências", expanded=False):
            st.caption("Exemplos ilustrativos · toque para selecionar.")
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

        if "nexus_fish_voice_name" not in st.session_state:
            st.session_state["nexus_fish_voice_name"] = ""

        if not fish_api_key:
            st.warning("Configure FISH_API_KEY nos Secrets do Streamlit para carregar as vozes.")
        else:
            selected_name = st.session_state.get("nexus_fish_voice_name") or "Nenhuma voz selecionada"
            st.markdown("**NARRAÇÃO**")
            st.text(selected_name)
            st.caption("Fish Audio · vozes profissionais de narração em português")
            with st.expander("🎙️ Escolher voz", expanded=False):
                st.caption("Seleção enxuta de vozes humanas para narração. Personagens, memes, anime e imitações de figuras públicas são excluídos.")
                catalog_key = "fish_professional_narrators_v1"
                if catalog_key not in st.session_state:
                    try:
                        with st.spinner("Carregando vozes profissionais masculinas e femininas..."):
                            st.session_state[catalog_key] = fish_audio.list_fish_professional_narrators(
                                fish_api_key, per_gender=25
                            )
                    except Exception as catalog_error:
                        st.session_state[catalog_key] = {"error": str(catalog_error)}
                narrator_catalog = st.session_state[catalog_key]
                if isinstance(narrator_catalog, dict) and narrator_catalog.get("error"):
                    st.error(f"Não foi possível carregar as vozes Fish Audio: {narrator_catalog['error']}")
                    if st.button("Tentar novamente", key="retry_professional_voices"):
                        st.session_state.pop(catalog_key, None)
                        st.rerun()
                else:
                    for gender, label in (("male", "Vozes masculinas"), ("female", "Vozes femininas")):
                        voices = narrator_catalog.get(gender, [])
                        with st.expander(f"{label} · {len(voices)} vozes", expanded=(gender == "male")):
                            if not voices:
                                st.info("A Fish Audio não retornou vozes compatíveis com os filtros nesta categoria.")
                            for voice_option in voices:
                                voice_col, sample_col = st.columns([1.1, 1.5], vertical_alignment="center")
                                with voice_col:
                                    is_selected = voice_option["id"] == st.session_state.get("nexus_fish_voice_id", "")
                                    st.markdown(f"**{voice_option['title']}**")
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
                                    if st.button(
                                        "Selecionada" if is_selected else "Usar esta voz",
                                        key=f"fish_pick_{voice_option['id']}",
                                        use_container_width=True,
                                        type="primary" if is_selected else "secondary",
                                    ):
                                        st.session_state["nexus_fish_voice_id"] = voice_option["id"]
                                        st.session_state["nexus_fish_voice_name"] = voice_option["title"]
                                        st.rerun()
                                with sample_col:
                                    if voice_option.get("sample_audio"):
                                        st.audio(voice_option["sample_audio"], format="audio/mp3")
                                    else:
                                        st.caption("Amostra não publicada pela Fish Audio.");

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
