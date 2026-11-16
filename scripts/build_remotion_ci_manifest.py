from pathlib import Path
from nexus.remotion_renderer import build_remotion_manifest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "remotion" / "public"
INPUT = PUBLIC / "ci-input"
INPUT.mkdir(parents=True, exist_ok=True)

plan = {
    "seo": {"title": "NEXUS Remotion integration check"},
    "scenes": [{
        "id": "ci-video-scene",
        "duration_seconds": 4,
        "voiceover": "Teste de integração do renderizador Remotion.",
        "visual_action": "Clipe de teste gerado pelo FFmpeg para validar a camada de vídeo.",
    }],
}
media = [{"path": str(INPUT / "sample.mp4")}]
manifest_path, manifest = build_remotion_manifest(
    plan,
    media,
    INPUT / "narration.wav",
    INPUT / "captions.srt",
    PUBLIC,
    job_id="ci",
)
print(f"Manifesto gerado: {manifest_path}")
print(f"Duração: {manifest['durationInFrames']} frames")
print(f"Cenas: {len(manifest['scenes'])}; legendas: {len(manifest['captions'])}")
