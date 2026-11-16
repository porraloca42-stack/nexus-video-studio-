from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nexus.remotion_renderer import build_remotion_manifest

PUBLIC = ROOT / "remotion" / "public"
INPUT = PUBLIC / "ci-input"
INPUT.mkdir(parents=True, exist_ok=True)

plan = {
    "seo": {"title": "NEXUS Remotion motion-beat integration check"},
    "scenes": [{
        "id": "ci-motion-scene",
        "duration_seconds": 4,
        "voiceover": "Teste de integração dos movimentos do renderizador Remotion.",
        "visual_action": "Imagem sintética vertical com movimento de câmera e dois microeventos visuais.",
        "image_prompt": "Synthetic test chart, high contrast shapes, vertical composition.",
        "camera_motion": "pan_left",
        "motion_events": [
            "A câmera avança no início da fala",
            "Um pulso visual destaca o assunto no segundo beat",
        ],
        "scene_direction": {
            "camera": {
                "move": "pan_left",
                "intensity": 0.9,
                "start_scale": 1.03,
                "end_scale": 1.22,
                "focus": "subject",
            },
            "depth_layers": {
                "foreground": "test shapes",
                "subject": "central test target",
                "background": "synthetic color field",
                "parallax_strength": 0.35,
            },
            "lighting": {"mood": "high contrast", "key_direction": "front", "change": "light_sweep"},
            "atmosphere": {"effect": "particles", "intensity": 0.25},
            "transition": {"in": "cut", "out": "cut", "duration_frames": 8},
            "beats": [
                {"at": 0.32, "event": "camera punch", "visual_target": "subject"},
                {"at": 0.72, "event": "accent pulse", "visual_target": "subject"},
            ],
        },
    }],
}
media = [{"path": str(INPUT / "sample.png")}]
manifest_path, manifest = build_remotion_manifest(
    plan,
    media,
    INPUT / "narration.wav",
    PUBLIC,
    job_id="ci",
)
print(f"Manifesto gerado: {manifest_path}")
print(f"Duração: {manifest['durationInFrames']} frames")
print(f"Cenas: {len(manifest['scenes'])}; narração: {bool(manifest['narrationAudio'])}")
print(f"Modo visual: {manifest['scenes'][0]['visualMode']}; microeventos: {len(manifest['scenes'][0]['motionEvents'])}")
