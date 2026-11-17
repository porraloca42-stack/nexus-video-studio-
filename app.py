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

from nexus.visual_styles import STYLE_OPTIONS, STYLE_META, STYLE_PROFILES

def style_preview_svg(style):
    sky, accent, ground, _ = STYLE_META[style]
    # Abstract material/lighting study only: no people, props, locations or scene examples.
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="270" viewBox="0 0 480 270">
      <defs>
        <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{sky}"/><stop offset="1" stop-color="{ground}"/></linearGradient>
        <radialGradient id="glow"><stop stop-color="{accent}" stop-opacity=".8"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>
        <pattern id="grain" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="{accent}" opacity=".22"/></pattern>
      </defs>
      <rect width="480" height="270" fill="url(#bg)"/>
      <ellipse cx="245" cy="128" rx="190" ry="110" fill="url(#glow)" opacity=".8"/>
      <g fill="none" stroke="{accent}" stroke-opacity=".72">
        <ellipse cx="240" cy="135" rx="175" ry="62" stroke-width="2"/>
        <ellipse cx="240" cy="135" rx="125" ry="95" stroke-width="1.5" transform="rotate(-28 240 135)"/>
        <ellipse cx="240" cy="135" rx="125" ry="95" stroke-width="1.5" transform="rotate(28 240 135)"/>
        <path d="M35 205 Q145 150 240 205 T445 205" stroke-width="3"/>
        <path d="M35 220 Q145 165 240 220 T445 220" stroke-width="1.5"/>
      </g>
      <circle cx="240" cy="135" r="34" fill="{accent}" opacity=".18"/>
      <circle cx="240" cy="135" r="8" fill="{accent}"/>
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
.block-container{padding-top:2rem!important;padding-bottom:3rem!important;max-width:1280px!important}
.nexus-hero{position:relative;overflow:hidden;padding:1.45rem 1.65rem;border:1px solid #30234d;border-radius:22px;background:linear-gradient(115deg,rgba(24,18,43,.98),rgba(18,18,22,.96) 65%,rgba(30,24,52,.95));box-shadow:0 18px 48px rgba(0,0,0,.38),inset 0 1px 0 rgba(255,255,255,.06);margin-bottom:1rem}
.nexus-brand-lockup{display:flex;align-items:center;justify-content:center;gap:clamp(.65rem,2.8vw,1.15rem);width:100%;min-width:0;margin:0 auto}
.nexus-logo-mark{display:grid;place-items:center;width:clamp(58px,16vw,76px);height:clamp(58px,16vw,76px);flex:0 0 auto;border-radius:18px;background:linear-gradient(145deg,#21163e,#101019);border:1px solid #6245a2;box-shadow:0 0 28px rgba(139,92,246,.22),inset 0 1px 0 rgba(255,255,255,.12)}.nexus-logo-mark svg{width:66%;height:66%;filter:drop-shadow(0 0 9px rgba(167,139,250,.45))}
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
[data-testid="stTextArea"] textarea{line-height:1.55!important;min-height:112px!important}
.st-key-nexus-bottom-nav{position:fixed!important;z-index:9999!important;left:0!important;right:0!important;bottom:0!important;width:100%!important;padding:.55rem 1rem calc(.55rem + env(safe-area-inset-bottom))!important;background:rgba(12,12,18,.96)!important;border-top:1px solid #30234d!important;backdrop-filter:blur(18px)!important}
.st-key-nexus-bottom-nav [data-testid="stRadio"]{margin:0!important}
.st-key-nexus-bottom-nav [role="radiogroup"]{display:flex!important;justify-content:space-around!important;gap:.25rem!important}
.st-key-nexus-bottom-nav [role="radiogroup"] label{flex:1 1 25%!important;justify-content:center!important;padding:.35rem .15rem!important;border-radius:10px!important;color:#a1a1aa!important;font-size:.78rem!important}
.st-key-nexus-bottom-nav [role="radiogroup"] label:has(input:checked){color:#c4b5fd!important;background:rgba(124,58,237,.14)!important}
.st-key-nexus-bottom-nav [role="radiogroup"] label p{font-size:.78rem!important}
.st-key-nexus-bottom-nav [role="radiogroup"] input{display:none!important}
.st-key-nexus-style-chips [role="radiogroup"]{display:flex!important;flex-wrap:nowrap!important;overflow-x:auto!important;gap:.45rem!important;padding:.25rem .05rem .65rem!important;scrollbar-width:thin!important}
.st-key-nexus-style-chips [role="radiogroup"] label{flex:0 0 auto!important;padding:.45rem .85rem!important;border:1px solid #34303f!important;border-radius:999px!important;background:#18181d!important;color:#d4d4d8!important}
.st-key-nexus-style-chips [role="radiogroup"] label:has(input:checked){border-color:#8b5cf6!important;background:rgba(124,58,237,.2)!important;color:#fff!important}
.st-key-nexus-style-chips [role="radiogroup"] input{display:none!important}
.nexus-output-placeholder{width:min(100%,290px);aspect-ratio:9/16;margin:1rem auto;border:1px solid #4b3b70;border-radius:22px;background:linear-gradient(145deg,#181522,#101014);display:flex;align-items:center;justify-content:center;text-align:center;color:#85808f;padding:1.2rem;box-shadow:inset 0 0 45px rgba(124,58,237,.08)}
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
@media(max-width:850px){.block-container{padding:1rem .8rem 7rem!important}.nexus-hero{padding:1rem .7rem;border-radius:17px}.nexus-brand-lockup{gap:.65rem}.nexus-brand-name{font-size:clamp(1.45rem,6.4vw,1.9rem);letter-spacing:.08em}.nexus-brand-subtitle{font-size:clamp(.72rem,3.1vw,.92rem);letter-spacing:.15em}.nexus-preview img{width:112px}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="nexus-hero"><div class="nexus-brand-lockup">
<div class="nexus-logo-mark" aria-label="NEXUS"><svg viewBox="0 0 64 64" aria-hidden="true"><path d="M32 3 39 23 59 32 39 39 32 61 24 40 4 32 24 24Z" fill="#9B7BFF"/><path d="M32 17 36 28 47 32 36 36 32 47 28 36 17 32 28 28Z" fill="#E9DFFF"/></svg></div>
<div class="nexus-brand-copy"><div class="nexus-brand-name">NEXUS</div><div class="nexus-brand-subtitle">VIDEO STUDIO</div></div>
</div></div>
""", unsafe_allow_html=True)



# Mobile-first navigation; the production pipeline is preserved.
with st.container(key="nexus-bottom-nav"):
    active_view = st.radio("Navegação", ["Criar", "Biblioteca", "Modelos", "Perfil"],
        horizontal=True, label_visibility="collapsed", key="nexus_navigation")

if active_view == "Criar":
    if "nexus_style" not in st.session_state or st.session_state["nexus_style"] not in STYLE_OPTIONS:
        st.session_state["nexus_style"] = "Cinematográfico"
    
    col_editor, col_preview = st.container(), st.container()
    
    with col_editor:
        with st.container(border=True):
            st.markdown('<div class="nexus-kicker">01 · Conteúdo</div>', unsafe_allow_html=True)
            topic = st.text_area("Assunto ou roteiro", height=105, placeholder="Descreva a ideia ou cole seu roteiro completo...")
            duration = st.selectbox("Duração", [40, 50, 60], index=1, format_func=lambda value: f"{value}s")
        with st.expander("Configurações avançadas de produção", expanded=False):
            st.markdown('<div class="nexus-kicker">PRODUÇÃO</div>', unsafe_allow_html=True)
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
            st.markdown('<div class="nexus-kicker">ESTILO VISUAL</div>', unsafe_allow_html=True)
            with st.container(key="nexus-style-chips"):
                st.radio("Estilo visual", STYLE_OPTIONS,
                    index=STYLE_OPTIONS.index(st.session_state["nexus_style"]),
                    horizontal=True, key="nexus_style", label_visibility="collapsed")
            style = st.session_state["nexus_style"]
            preview_svg = style_preview_svg(style)
            preview_b64 = base64.b64encode(preview_svg.encode("utf-8")).decode("ascii")
            preview_copy = STYLE_META[style][3]
            st.markdown(
                f'<div class="nexus-preview"><img src="data:image/svg+xml;base64,{preview_b64}" alt="Tratamento visual {style}"><div><div class="nexus-preview-title">{style}</div><div class="nexus-preview-copy">{preview_copy}</div></div></div>',
                unsafe_allow_html=True
            )
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
    
    if not st.session_state.get("nexus_rendered_video"):
        st.markdown('<div class="nexus-output-placeholder"><div><strong>PRÉVIA DO VÍDEO · 9:16</strong>Seu vídeo aparecerá aqui depois da geração</div></div>', unsafe_allow_html=True)
    
    if st.button("Gerar vídeo", type="primary", use_container_width=True):
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
    for label, key in [("Direção Gemini", "GEMINI_API_KEY"), ("Narração Fish Audio", "FISH_API_KEY"), ("Render remoto GitHub", "GITHUB_ACTIONS_TOKEN"), ("Geração visual Cloudflare", "CLOUDFLARE_API_TOKEN")]:
        if secret(key):
            st.success(f"{label} · configurado")
        else:
            st.warning(f"{label} · não configurado")
    st.divider()
    st.markdown("**Motor visual**")
    st.caption("Padrão: keyframes FLUX.2 Klein, animação Modal/LTX-Video e composição Remotion.")
    st.markdown("[Abrir o repositório do NEXUS](https://github.com/porraloca42-stack/nexus-video-studio-)")
