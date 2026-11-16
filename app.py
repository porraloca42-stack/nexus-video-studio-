import base64, json, os, subprocess, tempfile
from pathlib import Path
import streamlit as st
from nexus.director import create_storyboard, validate_storyboard
from nexus.assets import search_video_sources, search_coverr_videos, download_file
from nexus.audio import make_voice
from nexus.render import render_video

def secret(name, default=""):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)

st.set_page_config(page_title="NEXUS VIDEO STUDIO", page_icon="🎬", layout="wide")

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

STYLE_PREVIEWS = {
    "Cinematográfico realista": ("#182638", "#d59b58", "#526b78", "Luz natural, profundidade e contraste de cinema."),
    "Documentário cinematográfico": ("#263b35", "#d4bd83", "#758b71", "Textura natural e sensação observacional."),
    "Dark cinematográfico": ("#101522", "#8b76a8", "#30384f", "Sombras profundas e luz recortada."),
    "Filme noir": ("#101319", "#d6d1c5", "#454b56", "Preto e branco, sombras dramáticas."),
    "Publicidade premium": ("#26364b", "#f0c77b", "#8a9da8", "Acabamento limpo, luz controlada e composição elegante."),
    "Lifestyle realista": ("#b5c7c6", "#f2c78d", "#647f75", "Cores acolhedoras e momentos cotidianos."),
    "Natureza documental": ("#193b35", "#e6c77b", "#668d62", "Verdes orgânicos e luz ambiente."),
    "Minimalista clean": ("#dce5e8", "#f2c987", "#9bb1b8", "Poucos elementos e espaço visual."),
    "Vintage filme 35mm": ("#493a32", "#d6a46c", "#8d7254", "Grão suave e tons analógicos quentes."),
    "VHS retrô": ("#25234b", "#f0789b", "#3c8292", "Cores deslocadas e estética de fita."),
    "Cyberpunk neon": ("#171a3b", "#ff4fa3", "#16c8d2", "Neon magenta e ciano em alto contraste."),
    "Ficção científica futurista": ("#132b43", "#78d8e8", "#5274a5", "Luz tecnológica e atmosfera futurista."),
    "Fantasia cinematográfica": ("#29264c", "#f0c16e", "#78689d", "Luz mágica, atmosfera épica e cores ricas."),
    "Surrealismo fotográfico": ("#39405b", "#e9a6b1", "#8b9d9a", "Combinações oníricas com aparência fotográfica."),
    "Anime 2D": ("#7ab8d5", "#ffdc83", "#e28d83", "Cores ilustradas, contornos e céu expressivo."),
    "Anime 3D": ("#526b9a", "#f6c77c", "#9a8ac2", "Personagens e cenários estilizados em volume."),
    "Ilustração editorial": ("#e4d6b9", "#d78b63", "#63818a", "Formas gráficas e paleta editorial."),
    "Aquarela artística": ("#c4d9d2", "#edc58e", "#8aaeb1", "Pigmentos suaves e bordas orgânicas."),
    "Graphic novel": ("#252b38", "#e5b44f", "#a94d50", "Contraste forte, blocos de cor e traço marcado."),
    "3D realista": ("#29465b", "#f2c67b", "#7294a0", "Materiais, volume e iluminação realistas."),
    "3D estilizado": ("#546c9b", "#ffd27b", "#9c83c5", "Formas tridimensionais com cores estilizadas."),
    "Stop motion": ("#6e5142", "#e6bd78", "#8b9b72", "Textura artesanal e sensação de miniatura."),
    "Macro e detalhes": ("#183c43", "#e6b96d", "#6b9b91", "Enquadramentos próximos e foco seletivo."),
    "Drone e paisagens aéreas": ("#39728a", "#f2cb83", "#6e9d83", "Escala ampla e perspectiva aérea.")
}

def style_preview_svg(style):
    sky, sun, ground, _ = STYLE_PREVIEWS[style]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="270" viewBox="0 0 480 270">
    <defs>
      <linearGradient id="sky" x2="0" y2="1"><stop stop-color="{sky}"/><stop offset="1" stop-color="{ground}"/></linearGradient>
      <radialGradient id="glow"><stop stop-color="{sun}" stop-opacity=".9"/><stop offset="1" stop-color="{sun}" stop-opacity="0"/></radialGradient>
      <filter id="soft"><feGaussianBlur stdDeviation="15"/></filter>
    </defs>
    <rect width="480" height="270" fill="url(#sky)"/>
    <circle cx="350" cy="83" r="76" fill="url(#glow)"/>
    <circle cx="350" cy="83" r="27" fill="{sun}" opacity=".92"/>
    <path d="M0 190 L95 105 L165 177 L255 92 L365 190 L430 130 L480 176 L480 270 L0 270Z" fill="{ground}" opacity=".95"/>
    <path d="M0 215 Q115 165 220 218 T480 205 L480 270 L0 270Z" fill="#101820" opacity=".48"/>
    <path d="M0 244 Q110 220 220 244 T480 235 L480 270 L0 270Z" fill="#0b121b" opacity=".58"/>
    <path d="M0 0 H480 V270 H0Z" fill="none" stroke="{sun}" stroke-opacity=".25" stroke-width="5"/>
    <circle cx="85" cy="70" r="2" fill="#fff" opacity=".65"/><circle cx="125" cy="48" r="1.5" fill="#fff" opacity=".6"/>
    <circle cx="425" cy="42" r="2" fill="#fff" opacity=".5"/>
    </svg>'''
    return base64.b64encode(svg.encode("utf-8")).decode("ascii")

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1050px;}
.nexus-hero {padding: 1.15rem 1.2rem; border: 1px solid rgba(190,160,105,.28); border-radius: 18px; background: linear-gradient(135deg, rgba(190,160,105,.15), rgba(30,39,55,.55)); margin-bottom: 1.1rem;}
.nexus-kicker {font-size: .76rem; letter-spacing: .16em; text-transform: uppercase; color: #c9aa73; font-weight: 700;}
.nexus-sub {color: #aab1bd; font-size: .95rem; margin-top: .25rem;}
.nexus-preview {display:flex; gap:12px; align-items:center; padding:10px; border:1px solid rgba(160,170,185,.2); border-radius:14px; background:rgba(255,255,255,.035); margin:.25rem 0 1rem 0;}
.nexus-preview img {width:142px; max-width:42%; aspect-ratio:16/9; object-fit:cover; border-radius:9px;}
.nexus-preview-title {font-weight:700; margin-bottom:4px;}
.nexus-preview-copy {font-size:.82rem; color:#aab1bd; line-height:1.35;}
.nexus-step {font-size:.78rem; font-weight:700; color:#c9aa73; letter-spacing:.08em; text-transform:uppercase; margin-bottom:.2rem;}
div[data-testid="stButton"] button[kind="primary"] {border-radius:12px; min-height:3.1rem; font-weight:700;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nexus-hero"><div class="nexus-kicker">NEXUS VIDEO STUDIO</div><h1 style="margin:.25rem 0 0 0;">Transforme seu roteiro em vídeo</h1><div class="nexus-sub">Direção por IA · cenas coerentes · vídeo vertical</div></div>', unsafe_allow_html=True)
st.markdown('<div class="nexus-step">01 · Conteúdo</div>', unsafe_allow_html=True)
topic = st.text_area("Assunto ou roteiro", height=155, placeholder="Cole seu roteiro completo ou descreva o vídeo que deseja criar.")

st.markdown('<div class="nexus-step">02 · Direção visual</div>', unsafe_allow_html=True)
style = st.selectbox("Escolha a linguagem visual do vídeo", STYLE_OPTIONS, help="O estilo será enviado ao diretor de IA e aplicado às buscas de clipes de todas as cenas.")
preview_b64 = style_preview_svg(style)
preview_copy = STYLE_PREVIEWS[style][3]
st.markdown(
    f'<div class="nexus-preview"><img src="data:image/svg+xml;base64,{preview_b64}" alt="Prévia ilustrativa do estilo {style}"><div><div class="nexus-preview-title">{style}</div><div class="nexus-preview-copy">{preview_copy}<br><span style="opacity:.72">Prévia ilustrativa da linguagem visual</span></div></div></div>',
    unsafe_allow_html=True
)

st.markdown('<div class="nexus-step">03 · Configurações</div>', unsafe_allow_html=True)
settings_col1, settings_col2 = st.columns(2)
with settings_col1:
    duration = st.selectbox("Duração do vídeo", [40, 50, 60], index=1, format_func=lambda value: f"{value} segundos")
with settings_col2:
    voice = st.selectbox("Voz da narração", ["pt-BR-AntonioNeural", "pt-BR-FranciscaNeural", "pt-BR-ThalitaNeural"], format_func=lambda value: {"pt-BR-AntonioNeural":"Antônio · Masculina", "pt-BR-FranciscaNeural":"Francisca · Feminina", "pt-BR-ThalitaNeural":"Thalita · Feminina"}[value])

with st.expander("Ferramentas avançadas · diagnóstico da biblioteca Coverr"):
    st.caption("Ferramenta técnica para verificar a conexão e o download interno. Não é necessária para planejar ou produzir um vídeo.")
    if st.button("Testar conexão e download Coverr", type="secondary"):
        coverr_key = secret("COVERR_API_KEY")
        if not coverr_key:
            st.error("COVERR_API_KEY não encontrada nos Secrets.")
        else:
            with st.spinner("Verificando a biblioteca Coverr..."):
                try:
                    test_results = search_coverr_videos("nature landscape", coverr_key, per_page=5)
                    if not test_results:
                        st.warning("A API respondeu, mas não retornou clipes com URL MP4.")
                    else:
                        chosen = next((item for item in test_results if item.get("vertical")), test_results[0])
                        with tempfile.TemporaryDirectory(prefix="nexus_coverr_test_") as temp_dir:
                            clip_path = download_file(chosen["url"], Path(temp_dir) / "coverr_test.mp4")
                            probe = subprocess.run(
                                ["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,codec_type,width,height", "-of", "json", str(clip_path)],
                                capture_output=True, text=True, timeout=60
                            )
                            if probe.returncode != 0:
                                raise RuntimeError(probe.stderr[-1500:] or "FFprobe não conseguiu ler o arquivo.")
                            metadata = json.loads(probe.stdout)
                            streams = metadata.get("streams", [])
                            video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
                            if not video:
                                raise RuntimeError("O arquivo não contém uma faixa de vídeo.")
                            duration_seconds = float(metadata.get("format", {}).get("duration") or 0)
                            size_bytes = int(metadata.get("format", {}).get("size") or clip_path.stat().st_size)
                            if duration_seconds <= 0 or size_bytes <= 0:
                                raise RuntimeError("O arquivo baixado não apresentou duração ou tamanho válidos.")
                            st.success(f"Coverr respondeu e o download interno foi validado: {len(test_results)} clipes encontrados.")
                            st.caption(f"{chosen.get('title') or 'Clipe Coverr'} · {video.get('width')}×{video.get('height')} · {duration_seconds:.1f}s · {video.get('codec_name', 'codec desconhecido')}")
                except Exception as exc:
                    st.error(f"Falha no teste Coverr: {exc}")

if st.button("Planejar vídeo", type="primary", use_container_width=True):
    if not topic.strip():
        st.error("Informe um assunto ou roteiro.")
    elif not secret("GEMINI_API_KEY"):
        st.error("O serviço de direção ainda não está conectado.")
    else:
        with st.spinner("Analisando o conteúdo e dirigindo as cenas..."):
            try:
                plan = create_storyboard(topic, style, duration, secret)
                try:
                    errors = validate_storyboard(plan, duration)
                except TypeError:
                    # Compatibility while Streamlit refreshes an older cached module version.
                    errors = validate_storyboard(plan)
                    scenes = plan.get("scenes", [])
                    minimum = max(1, int((float(duration) + 4) // 5))
                    total = sum(float(scene.get("duration_seconds", 0) or 0) for scene in scenes)
                    if len(scenes) < minimum:
                        errors.append(f"O diretor criou {len(scenes)} cenas; são necessárias pelo menos {minimum}.")
                    if abs(total - float(duration)) > 0.75:
                        errors.append(f"A soma das cenas é {total:.1f}s; a duração solicitada é {duration}s.")
                    for scene_index, scene in enumerate(scenes, 1):
                        for field in ("visual_style", "style_search_terms"):
                            if not str(scene.get(field, "")).strip():
                                errors.append(f"Cena {scene_index}: campo {field} vazio.")
                st.session_state["nexus_plan"] = plan
                st.session_state["nexus_errors"] = errors
                st.session_state.pop("nexus_rendered_video", None)
                st.session_state.pop("nexus_rendered_info", None)
                if errors:
                    st.warning("O planejamento precisa de revisão: " + " ".join(errors))
                else:
                    st.success("Planejamento concluído.")
            except Exception as exc:
                st.error(str(exc))

if "nexus_plan" in st.session_state:
    plan = st.session_state["nexus_plan"]
    st.subheader("Direção audiovisual")
    st.write(plan.get("topic_interpretation", ""))
    st.write(plan.get("creative_thesis", ""))
    if plan.get("director_model"):
        st.caption("Modelo Gemini selecionado automaticamente: " + plan["director_model"])
    st.caption("Estilo visual solicitado: " + plan.get("style_lock", style))
    for i, scene in enumerate(plan.get("scenes", []), 1):
        with st.expander(f"Cena {i} · {scene.get('duration_seconds', 0)}s · {scene.get('purpose', '')}", expanded=True):
            st.markdown("**Narração**")
            st.write(scene.get("voiceover", ""))
            st.markdown("**Ação visual**")
            st.write(scene.get("visual_action", ""))
            st.markdown("**Estilo visual aplicado**")
            st.write(scene.get("visual_style", plan.get("style_lock", style)))
            if scene.get("style_search_terms"):
                st.caption("Termos de estilo para busca: " + scene.get("style_search_terms", ""))
            st.markdown("**Correspondência semântica**")
            st.write(scene.get("semantic_reason", ""))
            st.markdown("**Movimento e microeventos**")
            st.write(scene.get("camera_motion", ""))
            st.write(" → ".join(scene.get("motion_events", [])))
            st.caption("Busca visual: " + scene.get("asset_search_query", ""))

    if st.button("Produzir vídeo completo", type="primary", use_container_width=True):
        coverr_key = secret("COVERR_API_KEY")
        pixabay_key = secret("PIXABAY_API_KEY")
        if st.session_state.get("nexus_errors"):
            st.error("O storyboard precisa ser corrigido antes da produção.")
        elif not coverr_key and not pixabay_key:
            st.error("Conecte uma fonte de vídeos: COVERR_API_KEY ou PIXABAY_API_KEY.")
        else:
            st.session_state.pop("nexus_rendered_video", None)
            st.session_state.pop("nexus_rendered_info", None)
            work = Path(tempfile.mkdtemp(prefix="nexus_"))
            try:
                media, missing = [], []
                progress = st.progress(0, text="Preparando cenas...")
                for i, scene in enumerate(plan["scenes"]):
                    progress.progress((i + 1) / (len(plan["scenes"]) + 2), text=f"Buscando clipe para a cena {i + 1}/{len(plan['scenes'])}...")
                    style_terms = scene.get("style_search_terms", "")
                    primary_query = " ".join(part for part in [scene["asset_search_query"], style_terms] if part).strip()
                    fallback_query = " ".join(part for part in [scene.get("fallback_search_query", ""), style_terms] if part).strip()
                    candidates, source_errors = search_video_sources(primary_query, coverr_key, pixabay_key)
                    if not candidates and fallback_query:
                        candidates, retry_errors = search_video_sources(fallback_query, coverr_key, pixabay_key)
                        source_errors.extend(retry_errors)
                    if not candidates:
                        missing.append({
                            "scene": i + 1,
                            "query": primary_query,
                            "fallback": fallback_query,
                            "errors": source_errors,
                        })
                        continue
                    chosen = candidates[0]
                    path = download_file(chosen["url"], work / f"scene_{i:02d}.mp4")
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
                        "camera_motion": scene.get("camera_motion", "push_in"),
                        "source_title": chosen.get("title", ""),
                        "source_url": chosen.get("source_url", ""),
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
                            st.caption("Busca principal: " + item["query"])
                            if item["fallback"]:
                                st.caption("Busca alternativa: " + item["fallback"])
                            if item["errors"]:
                                for error in item["errors"]:
                                    st.caption(error)
                            else:
                                st.caption("A API respondeu, mas não encontrou resultados para as consultas tentadas.")
                else:
                    progress.progress((len(plan["scenes"]) + 1) / (len(plan["scenes"]) + 2), text="Gerando narração, legendas e montagem...")
                    narration = " ".join(scene["voiceover"] for scene in plan["scenes"])
                    audio, subtitles = make_voice(narration, voice, work / "voice.mp3")
                    output = work / "nexus_video.mp4"
                    render_video(media, audio, output, subtitles_path=subtitles)
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
                    if not final_video or not final_audio or final_duration <= 0 or output.stat().st_size == 0:
                        raise RuntimeError("O MP4 final não contém vídeo e áudio válidos.")
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
                    }
                    st.session_state["nexus_rendered_workdir"] = str(work)
                    progress.progress(1.0, text="Vídeo produzido e validado.")
                    st.success("Vídeo MP4 produzido. Áudio, vídeo e integridade do arquivo foram verificados.")
            except Exception as exc:
                st.exception(exc)

if st.session_state.get("nexus_rendered_video"):
    info = st.session_state.get("nexus_rendered_info", {})
    st.subheader("Seu vídeo está pronto")
    st.caption(f"{info.get('scene_count', 0)} cenas · {info.get('duration', 0):.1f}s · {info.get('width', 0)}×{info.get('height', 0)} · {info.get('size_mb', 0):.2f} MB")
    st.video(st.session_state["nexus_rendered_video"])
    st.download_button(
        "Baixar vídeo MP4",
        data=st.session_state["nexus_rendered_video"],
        file_name=st.session_state.get("nexus_rendered_filename", "nexus_video.mp4"),
        mime="video/mp4",
        use_container_width=True,
    )
