import base64, json, os, shutil, subprocess, tempfile
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
:root {color-scheme:dark;}
.block-container {padding-top:1.1rem;padding-bottom:3rem;max-width:980px;}
.nexus-hero {position:relative;overflow:hidden;padding:1.15rem 1.25rem 1.05rem;border:1px solid rgba(218,190,139,.35);border-radius:20px;background:radial-gradient(ellipse at 88% 8%,rgba(202,166,104,.22),transparent 38%),linear-gradient(145deg,#242a35 0%,#171b24 58%,#202632 100%);box-shadow:inset 0 1px 0 rgba(255,255,255,.12),0 12px 28px rgba(0,0,0,.28),0 2px 0 rgba(218,190,139,.18);}
.nexus-brand {font-size:1.32rem;font-weight:850;letter-spacing:.16em;color:#e2c38c;text-shadow:0 2px 12px rgba(218,190,139,.18);}
.nexus-tagline {font-size:.91rem;color:#d1d5dd;margin-top:.18rem;letter-spacing:.015em;}
.nexus-kicker {font-size:.75rem;letter-spacing:.13em;text-transform:uppercase;color:#d7bb87;font-weight:750;margin:1.35rem 0 .35rem;}
.nexus-preview {display:flex;gap:13px;align-items:center;padding:11px;border:1px solid rgba(210,190,155,.28);border-radius:16px;background:linear-gradient(145deg,rgba(255,255,255,.075),rgba(255,255,255,.025));box-shadow:inset 0 1px 0 rgba(255,255,255,.08),0 7px 18px rgba(0,0,0,.18);margin:.35rem 0 .65rem;}
.nexus-preview img {width:148px;max-width:42%;aspect-ratio:16/9;object-fit:cover;border-radius:10px;box-shadow:0 4px 12px rgba(0,0,0,.28);}
.nexus-preview-title {font-weight:750;margin-bottom:4px;}
.nexus-preview-copy {font-size:.82rem;color:#b8c0cb;line-height:1.4;}
.nexus-card-label {font-size:.82rem;font-weight:700;margin:.1rem 0 .4rem;color:#e6e9ef;}
/* Use a true two-column grid: Streamlit's flex columns were overflowing on narrow mobile screens. */
div.st-key-nexus-style-gallery {display:block !important; width:100% !important; max-width:100% !important; min-width:0 !important; overflow-x:hidden !important; box-sizing:border-box !important;}
div.st-key-nexus-style-gallery div[data-testid="stHorizontalBlock"] {display:grid !important; grid-template-columns:repeat(2,minmax(0,1fr)) !important; width:100% !important; max-width:100% !important; min-width:0 !important; column-gap:.55rem !important; row-gap:.7rem !important; margin-bottom:.7rem !important; overflow:hidden !important; box-sizing:border-box !important;}
div.st-key-nexus-style-gallery div[data-testid="column"] {display:block !important; width:100% !important; max-width:100% !important; min-width:0 !important; flex:none !important; overflow:hidden !important; box-sizing:border-box !important;}
div.st-key-nexus-style-gallery div[data-testid="column"] > div {width:100% !important; max-width:100% !important; min-width:0 !important; box-sizing:border-box !important;}
div.st-key-nexus-style-gallery div[data-testid="stImage"] {display:block !important; position:relative !important; width:100% !important; max-width:100% !important; min-width:0 !important; margin:0 auto .15rem !important; text-align:center !important; overflow:visible !important;}
div.st-key-nexus-style-gallery div[data-testid="stImage"] > div {display:block !important; width:100% !important; max-width:100% !important; margin:0 auto !important; text-align:center !important;}
div.st-key-nexus-style-gallery div[data-testid="stImage"] img {display:block !important; position:relative !important; left:50% !important; transform:translateX(-50%) !important; width:85px !important; min-width:85px !important; max-width:85px !important; height:auto !important; margin:0 !important;}
div.st-key-nexus-style-gallery div[data-testid="stButton"] {display:flex !important; justify-content:center !important; width:100% !important; max-width:100% !important; min-width:0 !important;}
div.st-key-nexus-style-gallery div[data-testid="stButton"] button {display:flex !important; align-items:center !important; justify-content:center !important; width:78% !important; max-width:155px !important; min-width:0 !important; margin-left:auto !important; margin-right:auto !important; height:auto !important; min-height:1.8rem !important; padding:.2rem .25rem !important; white-space:normal !important; overflow:visible !important; text-overflow:clip !important; overflow-wrap:break-word !important; word-break:normal !important; font-size:.62rem !important; line-height:1.1 !important; box-sizing:border-box !important;}
div.st-key-nexus-style-gallery div[data-testid="stButton"] button *,
div.st-key-nexus-style-gallery div[data-testid="stButton"] button div,
div.st-key-nexus-style-gallery div[data-testid="stButton"] button p,
div.st-key-nexus-style-gallery div[data-testid="stButton"] button span {display:block !important; width:100% !important; max-width:100% !important; min-width:0 !important; height:auto !important; max-height:none !important; margin:0 !important; padding:0 !important; font-size:.62rem !important; line-height:1.1 !important; white-space:normal !important; overflow:visible !important; text-overflow:clip !important; overflow-wrap:break-word !important; word-break:normal !important;}

div[data-testid="stButton"] button {border-radius:12px;min-height:2.65rem;border:1px solid rgba(210,190,155,.24);box-shadow:0 3px 10px rgba(0,0,0,.16);}
div[data-testid="stButton"] button[kind="primary"] {border-color:rgba(222,190,132,.7);box-shadow:inset 0 1px 0 rgba(255,255,255,.16),0 5px 15px rgba(194,157,94,.2);font-weight:750;}
div[data-testid="stTextArea"] textarea,div[data-testid="stSelectbox"] div[data-baseweb="select"] {border-radius:13px;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nexus-hero"><div class="nexus-brand">NEXUS VIDEO STUDIO</div><div class="nexus-tagline">Transforme seu roteiro em vídeo</div></div>', unsafe_allow_html=True)

if "nexus_style" not in st.session_state or st.session_state["nexus_style"] not in STYLE_OPTIONS:
    st.session_state["nexus_style"] = "Cinematográfico realista"

st.markdown('<div class="nexus-kicker">01 · Conteúdo</div>', unsafe_allow_html=True)
topic = st.text_area("Assunto ou roteiro", height=145, placeholder="Cole seu roteiro completo ou descreva o vídeo que deseja criar.")

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

st.markdown('<div class="nexus-kicker">03 · Configurações</div>', unsafe_allow_html=True)
settings_col1, settings_col2 = st.columns(2)
with settings_col1:
    duration = st.selectbox("Duração do vídeo", [40, 50, 60], index=1, format_func=lambda value: f"{value} segundos")
with settings_col2:
    voice = st.selectbox("Voz da narração", ["pt-BR-AntonioNeural", "pt-BR-FranciscaNeural", "pt-BR-ThalitaNeural"], format_func=lambda value: {"pt-BR-AntonioNeural":"Antônio · Masculina", "pt-BR-FranciscaNeural":"Francisca · Feminina", "pt-BR-ThalitaNeural":"Thalita · Feminina"}[value])

with st.expander("Ferramentas avançadas · diagnóstico da biblioteca Coverr"):
    st.caption("Build do aplicativo: NEXUS-2026.11.16-multi-source-1 · se esta identificação não aparecer, o Streamlit ainda está servindo uma versão anterior.")
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
        coverr_key = secret("COVERR_API_KEY")
        pixabay_key = secret("PIXABAY_API_KEY")
        pexels_key = secret("PEXELS_API_KEY")
        if st.session_state.get("nexus_errors"):
            st.error("O storyboard precisa ser corrigido antes da produção.")
        elif not coverr_key and not pixabay_key and not pexels_key:
            st.error("Conecte pelo menos uma fonte: COVERR_API_KEY, PIXABAY_API_KEY ou PEXELS_API_KEY.")
        else:
            st.session_state.pop("nexus_rendered_video", None)
            st.session_state.pop("nexus_rendered_info", None)
            work = Path(tempfile.mkdtemp(prefix="nexus_"))
            try:
                media, missing = [], []
                used_asset_urls = set()
                progress = st.progress(0, text="Preparando cenas...")
                for i, scene in enumerate(plan["scenes"]):
                    progress.progress((i + 1) / (len(plan["scenes"]) + 2), text=f"Buscando clipe para a cena {i + 1}/{len(plan['scenes'])}...")
                    style_terms = scene.get("style_search_terms", "")
                    primary_query = " ".join(part for part in [scene["asset_search_query"], style_terms] if part).strip()
                    fallback_query = " ".join(part for part in [scene.get("fallback_search_query", ""), style_terms] if part).strip()
                    candidates, source_errors = search_video_sources(
                        primary_query,
                        coverr_key,
                        pixabay_key,
                        pexels_key=pexels_key,
                        exclude_urls=used_asset_urls,
                        relevance_query=scene["asset_search_query"],
                    )
                    if not candidates and fallback_query:
                        candidates, retry_errors = search_video_sources(
                            fallback_query,
                            coverr_key,
                            pixabay_key,
                            pexels_key=pexels_key,
                            exclude_urls=used_asset_urls,
                            relevance_query=scene.get("fallback_search_query", scene["asset_search_query"]),
                        )
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
                    used_asset_urls.add(chosen["url"])
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
                    }
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
    st.video(st.session_state["nexus_rendered_video"])
    st.download_button(
        "Baixar vídeo MP4",
        data=st.session_state["nexus_rendered_video"],
        file_name=st.session_state.get("nexus_rendered_filename", "nexus_video.mp4"),
        mime="video/mp4",
        use_container_width=True,
    )
