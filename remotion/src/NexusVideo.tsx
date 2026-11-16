import React from "react";
import {
  AbsoluteFill,
  Audio,
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
  const accent = scene.accent || "#e8b66b";
  const drift = Math.sin(local / 32) * 18;
  const progress = Math.max(0, Math.min(1, local / Math.max(1, duration)));
  const motion = scene.cameraMotion || "push_in";
  // Stronger, continuous camera movement: a visible Ken Burns move rather than
  // the previous nearly imperceptible 6–8% drift. Motion remains camera-based;
  // still images do not become generated live-action footage.
  const imageScale = motion === "pull_out" ? 1.28 - progress * 0.16 : 1.12 + progress * 0.16;
  const imageX = motion === "pan_left" ? progress * 76 : motion === "pan_right" ? -progress * 76 : Math.sin(progress * Math.PI) * 10;
  const imageY = motion === "push_in" ? -progress * 34 : motion === "pull_out" ? progress * 26 : Math.sin(progress * Math.PI) * 8;
  const imageRotate = Math.sin(progress * Math.PI) * 0.45;

  return (
    <AbsoluteFill style={{ opacity: 1, overflow: "hidden", background: "#0b111a" }}>
      {scene.visualMode === "video" && scene.asset ? (
        <OffthreadVideo src={staticFile(scene.asset!)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : scene.visualMode === "image" && scene.asset ? (
        <Img src={staticFile(scene.asset!)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `translate(${imageX}px, ${imageY}px) scale(${imageScale}) rotate(${imageRotate}deg)` }} />
      ) : (
        <AbsoluteFill style={{ background: "radial-gradient(ellipse at 70% 30%, #33485d 0%, #172330 36%, #090e15 78%)" }}>
          <div style={{ position: "absolute", width: 680, height: 680, borderRadius: "50%", border: `1px solid ${accent}66`, right: -290 + drift, top: 190, boxShadow: `0 0 100px ${accent}22, inset 0 0 100px ${accent}12` }} />
          <div style={{ position: "absolute", width: 430, height: 430, borderRadius: "50%", border: `1px solid ${accent}55`, right: -165 - drift, top: 315, transform: `rotate(${local * 0.2}deg)` }} />
          <div style={{ position: "absolute", width: 12, height: 12, borderRadius: "50%", background: accent, right: 190 + drift, top: 440 + Math.sin(local / 18) * 95, boxShadow: `0 0 36px 12px ${accent}77` }} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #05080b66 0%, transparent 30%, #05080b88 100%)" }} />
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
