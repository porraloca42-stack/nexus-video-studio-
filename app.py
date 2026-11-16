import os, tempfile
from pathlib import Path
import streamlit as st
from nexus.director import create_storyboard, validate_storyboard
from nexus.assets import search_pexels_videos, download_file
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
                errors = validate_storyboard(plan)
                st.session_state["nexus_plan"] = plan
                st.session_state["nexus_errors"] = errors
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

    if st.button("Renderizar MP4", use_container_width=True):
        pexels_key = secret("PEXELS_API_KEY")
        if st.session_state.get("nexus_errors"):
            st.error("O storyboard precisa ser corrigido antes da renderização.")
        elif not pexels_key:
            st.error("A biblioteca de clipes ainda não está conectada.")
        else:
            work = Path(tempfile.mkdtemp(prefix="nexus_"))
            try:
                media, missing = [], []
                for i, scene in enumerate(plan["scenes"]):
                    candidates = search_pexels_videos(scene["asset_search_query"], pexels_key)
                    if not candidates and scene.get("fallback_search_query"):
                        candidates = search_pexels_videos(scene["fallback_search_query"], pexels_key)
                    if not candidates:
                        missing.append(i + 1)
                        continue
                    chosen = candidates[0]
                    path = download_file(chosen["url"], work / f"scene_{i:02d}.mp4")
                    media.append({"path": str(path), "duration": scene["duration_seconds"], "camera_motion": scene.get("camera_motion", "push_in")})
                if missing:
                    st.error(f"Não encontrei clipes para as cenas {missing}. Interrompi para evitar um vídeo visualmente incoerente.")
                else:
                    with st.spinner("Gerando narração, legendas e vídeo..."):
                        narration = " ".join(scene["voiceover"] for scene in plan["scenes"])
                        audio, subtitles = make_voice(narration, voice, work / "voice.mp3")
                        output = work / "nexus_video.mp4"
                        render_video(media, audio, output, subtitles_path=subtitles)
                    st.video(str(output))
                    st.download_button("Baixar MP4", output.read_bytes(), "nexus_video.mp4", "video/mp4")
            except Exception as exc:
                st.exception(exc)
