import json, os, subprocess, tempfile
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
st.title("NEXUS VIDEO STUDIO")
st.caption("Direção contextual por IA · Vídeos verticais")
st.info("O diretor interpreta o assunto completo, planeja cenas ligadas à narração e mantém o estilo visual escolhido em todo o vídeo.")

st.subheader("Teste da biblioteca Coverr")
st.caption("Este diagnóstico baixa o clipe temporariamente no servidor do NEXUS para testar a fonte. Nada é baixado no seu celular; o produto final será um único MP4 gerado pelo estúdio.")
if st.button("Testar Coverr: buscar e baixar clipe", type="secondary"):
    coverr_key = secret("COVERR_API_KEY")
    if not coverr_key:
        st.error("COVERR_API_KEY não encontrada nos Secrets.")
    else:
        with st.spinner("Buscando clipes na Coverr..."):
            try:
                test_results = search_coverr_videos("nature landscape", coverr_key, per_page=5)
                if not test_results:
                    st.warning("A API respondeu, mas não retornou clipes com URL MP4.")
                else:
                    st.success(f"Busca concluída: {len(test_results)} clipes encontrados.")
                    for item in test_results[:5]:
                        orientation = "vertical" if item.get("vertical") else "horizontal"
                        st.caption(f"{item.get('title') or 'Sem título'} · {item.get('width')}×{item.get('height')} · {orientation}")
                    chosen = next((item for item in test_results if item.get("vertical")), test_results[0])
                    st.info(f"Validando download interno: {chosen.get('title') or 'clipe Coverr'}")
                    with tempfile.TemporaryDirectory(prefix="nexus_coverr_test_") as temp_dir:
                        clip_path = download_file(chosen["url"], Path(temp_dir) / "coverr_test.mp4")
                        probe = subprocess.run(
                            ["ffprobe", "-v", "error", "-show_entries",
                             "format=duration,size:stream=codec_name,codec_type,width,height",
                             "-of", "json", str(clip_path)],
                            capture_output=True, text=True, timeout=60
                        )
                        if probe.returncode != 0:
                            raise RuntimeError(probe.stderr[-1500:] or "FFprobe não conseguiu ler o arquivo baixado.")
                        metadata = json.loads(probe.stdout)
                        streams = metadata.get("streams", [])
                        video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
                        if not video:
                            raise RuntimeError("O arquivo baixado não contém uma faixa de vídeo.")
                        duration_seconds = float(metadata.get("format", {}).get("duration") or 0)
                        size_bytes = int(metadata.get("format", {}).get("size") or clip_path.stat().st_size)
                        if duration_seconds <= 0 or size_bytes <= 0:
                            raise RuntimeError("O arquivo baixado não apresentou duração ou tamanho válidos.")
                        st.success("Download no servidor e integridade do arquivo confirmados. Nenhum arquivo foi enviado ao celular.")
                        st.write(f"**Resolução:** {video.get('width')} × {video.get('height')}")
                        st.write(f"**Codec:** {video.get('codec_name', 'não identificado')}")
                        st.write(f"**Duração:** {duration_seconds:.2f} segundos")
                        st.write(f"**Tamanho:** {size_bytes / (1024 * 1024):.2f} MB")
            except Exception as exc:
                st.error(f"Falha na busca ou validação do download Coverr: {exc}")

with st.sidebar:
    st.subheader("Produção")
    style = st.selectbox("Estilo visual", ["Cinematográfico realista", "Dark cinematográfico", "Documental realista", "Surrealista fotográfico", "Anime cinematográfico", "Graphic novel", "3D conceitual", "Vintage cinematográfico", "Cyberpunk"])
    voice = st.selectbox("Voz", ["pt-BR-AntonioNeural", "pt-BR-FranciscaNeural", "pt-BR-ThalitaNeural"])
    duration = st.selectbox("Duração", [40, 50, 60], index=1)

topic = st.text_area("Assunto ou roteiro", height=150, placeholder="Digite um assunto ou cole o roteiro completo.")
if st.button("Planejar vídeo", type="primary", use_container_width=True):
    if not topic.strip():
        st.error("Informe um assunto ou roteiro.")
    elif not secret("GEMINI_API_KEY"):
        st.error("O serviço de direção ainda não está conectado.")
    else:
        with st.spinner("Analisando o conteúdo e dirigindo as cenas..."):
            try:
                plan = create_storyboard(topic, style, duration, secret)
                errors = validate_storyboard(plan, duration)
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
    st.caption("Estilo bloqueado: " + plan.get("style_lock", style))
    for i, scene in enumerate(plan.get("scenes", []), 1):
        with st.expander(f"Cena {i} · {scene.get('duration_seconds', 0)}s · {scene.get('purpose', '')}", expanded=True):
            st.markdown("**Narração**")
            st.write(scene.get("voiceover", ""))
            st.markdown("**Ação visual**")
            st.write(scene.get("visual_action", ""))
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
                    candidates, source_errors = search_video_sources(scene["asset_search_query"], coverr_key, pixabay_key)
                    if not candidates and scene.get("fallback_search_query"):
                        candidates, retry_errors = search_video_sources(scene["fallback_search_query"], coverr_key, pixabay_key)
                        source_errors.extend(retry_errors)
                    if not candidates:
                        missing.append({
                            "scene": i + 1,
                            "query": scene.get("asset_search_query", ""),
                            "fallback": scene.get("fallback_search_query", ""),
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
