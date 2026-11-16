import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  Sequence,
  useCurrentFrame,
} from "remotion";

const scenes = [
  {
    eyebrow: "NEXUS VIDEO STUDIO",
    title: "Toda mudança\ncomeça por uma escolha.",
    detail: "O primeiro passo é enxergar além do cenário atual.",
    accent: "#e8b66b",
    motif: "orbit",
  },
  {
    eyebrow: "01  ·  CLAREZA",
    title: "Dê direção\naos seus pensamentos.",
    detail: "Uma ideia ganha força quando encontra intenção e foco.",
    accent: "#7cc9d4",
    motif: "rings",
  },
  {
    eyebrow: "02  ·  MOVIMENTO",
    title: "Transforme intenção\nem atitude.",
    detail: "Pequenas decisões constroem novos caminhos.",
    accent: "#c29be8",
    motif: "steps",
  },
  {
    eyebrow: "03  ·  CONSTÂNCIA",
    title: "Continue, mesmo\nsem aplausos.",
    detail: "O progresso real também acontece longe dos olhares.",
    accent: "#e6a18d",
    motif: "particles",
  },
  {
    eyebrow: "NEXUS VIDEO STUDIO",
    title: "Sua próxima história\ncomeça agora.",
    detail: "Roteiro, direção e composição em um só fluxo.",
    accent: "#e8b66b",
    motif: "orbit",
  },
];

const Scene: React.FC<{ scene: (typeof scenes)[number]; index: number }> = ({
  scene,
  index,
}) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 22], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const exit = interpolate(frame, [260, 300], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = Math.min(enter, exit);
  const drift = Math.sin(frame / 34) * 22;

  return (
    <AbsoluteFill
      style={{
        opacity,
        background:
          "radial-gradient(ellipse at 72% 26%, #27384a 0%, #111923 38%, #080d14 78%)",
        color: "#f7f2e9",
        fontFamily: "Arial, Helvetica, sans-serif",
        padding: "108px 64px 92px",
        justifyContent: "space-between",
        overflow: "hidden",
      }}
    >
      <AbsoluteFill style={{ opacity: 0.7, pointerEvents: "none" }}>
        <div
          style={{
            position: "absolute",
            width: 520,
            height: 520,
            borderRadius: "50%",
            border: `1px solid ${scene.accent}55`,
            right: -210 + drift,
            top: 130,
            transform: `scale(${0.82 + enter * 0.18})`,
            boxShadow: `0 0 90px ${scene.accent}22, inset 0 0 90px ${scene.accent}10`,
          }}
        />
        <div
          style={{
            position: "absolute",
            width: 330,
            height: 330,
            borderRadius: "50%",
            border: `1px solid ${scene.accent}66`,
            right: -115 - drift * 0.6,
            top: 225,
            transform: `rotate(${frame * 0.18}deg)`,
          }}
        />
        <div
          style={{
            position: "absolute",
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: scene.accent,
            right: 170 + drift,
            top: 280 + Math.sin(frame / 20) * 70,
            boxShadow: `0 0 28px 10px ${scene.accent}66`,
          }}
        />
      </AbsoluteFill>

      <div style={{ zIndex: 1, display: "flex", alignItems: "center", gap: 14 }}>
        <div style={{ width: 34, height: 2, background: scene.accent }} />
        <div style={{ fontSize: 17, letterSpacing: 4, color: scene.accent, fontWeight: 700 }}>
          {scene.eyebrow}
        </div>
      </div>

      <div style={{ zIndex: 1, marginTop: 130, transform: `translateY(${(1 - enter) * 42}px)` }}>
        <div
          style={{
            whiteSpace: "pre-line",
            fontSize: 66,
            lineHeight: 1.12,
            letterSpacing: -2.5,
            fontWeight: 700,
            maxWidth: 610,
            textShadow: "0 8px 40px #0009",
          }}
        >
          {scene.title}
        </div>
        <div
          style={{
            width: 76,
            height: 4,
            background: scene.accent,
            marginTop: 38,
            marginBottom: 28,
          }}
        />
        <div style={{ color: "#c0c8d0", fontSize: 25, lineHeight: 1.45, maxWidth: 530 }}>
          {scene.detail}
        </div>
      </div>

      <div style={{ zIndex: 1, display: "flex", justifyContent: "space-between", alignItems: "end" }}>
        <div style={{ fontSize: 15, letterSpacing: 3, color: "#82909d" }}>
          DESPERTE  ·  MANIFESTE
        </div>
        <div style={{ fontSize: 17, color: scene.accent, fontVariantNumeric: "tabular-nums" }}>
          0{index + 1} / 05
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const NexusDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, 1500], [0, 100], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#080d14" }}>
      {scenes.map((scene, index) => (
        <Sequence key={scene.eyebrow + index} from={index * 300} durationInFrames={300}>
          <Scene scene={scene} index={index} />
        </Sequence>
      ))}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          height: 4,
          width: `${progress}%`,
          background: "linear-gradient(90deg, #7cc9d4, #e8b66b)",
        }}
      />
    </AbsoluteFill>
  );
};
