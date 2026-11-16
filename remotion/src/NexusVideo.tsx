import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  OffthreadVideo,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { NexusCaption, NexusScene, NexusVideoProps } from "./types";

const SceneLayer: React.FC<{ scene: NexusScene; index: number; from: number; duration: number }> = ({
  scene, index, from, duration,
}) => {
  const frame = useCurrentFrame();
  const local = frame - from;
  const fade = Math.min(
    interpolate(local, [0, 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }),
    interpolate(local, [duration - 18, duration], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
  );
  const accent = scene.accent || "#e8b66b";
  const drift = Math.sin(local / 32) * 18;
  const progress = Math.max(0, Math.min(1, local / Math.max(1, duration)));
  const motion = scene.cameraMotion || "push_in";
  const imageScale = motion === "pull_out" ? 1.12 - progress * 0.07 : 1.06 + progress * 0.08;
  const imageX = motion === "pan_left" ? progress * 34 : motion === "pan_right" ? -progress * 34 : 0;
  const imageY = motion === "push_in" ? -progress * 16 : motion === "pull_out" ? progress * 12 : 0;

  return (
    <AbsoluteFill style={{ opacity: fade, overflow: "hidden", background: "#0b111a" }}>
      {scene.visualMode === "video" && scene.asset ? (
        <OffthreadVideo src={staticFile(scene.asset!)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : scene.visualMode === "image" && scene.asset ? (
        <Img src={staticFile(scene.asset!)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `translate(${imageX}px, ${imageY}px) scale(${imageScale})` }} />
      ) : (
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at 70% 30%, #33485d 0%, #172330 36%, #090e15 78%)" }}>
          <div style={{ position: "absolute", width: 680, height: 680, borderRadius: "50%", border: `1px solid ${accent}66`, right: -290 + drift, top: 190, boxShadow: `0 0 100px ${accent}22, inset 0 0 100px ${accent}12` }} />
          <div style={{ position: "absolute", width: 430, height: 430, borderRadius: "50%", border: `1px solid ${accent}55`, right: -165 - drift, top: 315, transform: `rotate(${local * 0.2}deg)` }} />
          <div style={{ position: "absolute", width: 12, height: 12, borderRadius: "50%", background: accent, right: 190 + drift, top: 440 + Math.sin(local / 18) * 95, boxShadow: `0 0 36px 12px ${accent}77` }} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #05080b66 0%, transparent 30%, #05080b88 100%)" }} />
      <div style={{ position: "absolute", top: 105, left: 62, right: 62 }}>
        <div style={{ color: accent, fontSize: 17, letterSpacing: 4, fontWeight: 700 }}>NEXUS VIDEO STUDIO</div>
        {scene.headline ? (
          <div style={{ marginTop: 540, color: "#fff", fontSize: 58, lineHeight: 1.12, fontWeight: 750, whiteSpace: "pre-line", textShadow: "0 8px 40px #000b" }}>{scene.headline}</div>
        ) : null}
        {scene.visualDescription ? (
          <div style={{ marginTop: 22, color: "#e4e9ed", fontSize: 23, lineHeight: 1.4, maxWidth: 570 }}>{scene.visualDescription}</div>
        ) : null}
      </div>
      <div style={{ position: "absolute", bottom: 64, left: 62, right: 62, display: "flex", justifyContent: "space-between", color: "#ffffffaa", fontSize: 15, letterSpacing: 2 }}>
        <span>ROTEIRO · DIREÇÃO · MOVIMENTO</span><span>{String(index + 1).padStart(2, "0")}</span>
      </div>
    </AbsoluteFill>
  );
};

const CaptionLayer: React.FC<{ captions: NexusCaption[] }> = ({ captions }) => {
  const frame = useCurrentFrame();
  const active = captions.find((caption) => frame >= caption.startFrame && frame < caption.endFrame);
  if (!active) return null;
  return (
    <div style={{ position: "absolute", left: 48, right: 48, bottom: 175, display: "flex", justifyContent: "center", textAlign: "center" }}>
      <div style={{ background: "#05080bcc", border: "1px solid #ffffff24", borderRadius: 12, padding: "13px 20px", color: "#fff", fontSize: 30, lineHeight: 1.2, fontWeight: 800, textShadow: "0 2px 5px #000", maxWidth: 620 }}>{active.text}</div>
    </div>
  );
};

export const NexusVideo: React.FC<NexusVideoProps> = (props) => {
  const { fps } = useVideoConfig();
  let cursor = 0;
  const layers = props.scenes.map((scene, index) => {
    const from = cursor;
    const duration = Math.max(1, Math.round(scene.durationSeconds * fps));
    cursor += duration;
    return { scene, index, from, duration };
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#080d14", fontFamily: "Arial, Helvetica, sans-serif" }}>
      {layers.map((layer) => (
        <SceneLayer key={layer.scene.id} {...layer} />
      ))}
      {props.narrationAudio ? <Audio src={staticFile(props.narrationAudio)} /> : null}
      {props.musicAudio ? <Audio src={staticFile(props.musicAudio)} volume={0.12} /> : null}
      <CaptionLayer captions={props.captions} />
    </AbsoluteFill>
  );
};
