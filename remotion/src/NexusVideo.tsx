import React from "react";
import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { NexusScene, NexusVideoProps } from "./types";

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));

const SceneLayer: React.FC<{ scene: NexusScene; duration: number; overlapFrames: number }> = ({ scene, duration, overlapFrames }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const accent = scene.accent || "#e8b66b";
  const direction = scene.sceneDirection;
  const camera = direction?.camera;
  const progress = clamp(frame / Math.max(1, duration - overlapFrames), 0, 1);
  const move = camera?.move || scene.cameraMotion || "push_in";
  const intensity = clamp(camera?.intensity ?? 0.72, 0, 1);
  const startScale = clamp(camera?.startScale ?? (move === "pull_out" ? 1.15 : 1.08), 1, 1.15);
  const endScale = clamp(camera?.endScale ?? (move === "pull_out" ? 1.0 : 1.15), 1, 1.15);
  const beatPulse = (direction?.beats || []).reduce((pulse, beat) => {
    const distance = Math.abs(frame - clamp(beat.at, 0, 1) * duration);
    return Math.max(pulse, distance < 7 ? (1 - distance / 7) * 0.018 : 0);
  }, 0);
  const scale = interpolate(progress, [0, 1], [startScale, endScale]) + beatPulse;
  const pan = 76 * intensity;
  const x = move === "pan_left" ? progress * pan : move === "pan_right" ? -progress * pan : 0;
  const y = move === "tilt_up" ? progress * pan : move === "tilt_down" ? -progress * pan : move === "push_in" ? -progress * 24 * intensity : 0;
  const mediaStyle: React.CSSProperties = {
    width: "100%", height: "100%", objectFit: "cover",
    transform: `translate(${x}px, ${y}px) scale(${scale})`,
    transformOrigin: camera?.focus === "foreground" ? "50% 75%" : camera?.focus === "background" ? "50% 25%" : "50% 50%",
  };
  const transitionFrames = direction?.transition?.durationFrames || overlapFrames;
  const fadeIn = direction?.transition?.in === "crossfade" ? clamp(transitionFrames, 1, 12) : 0;
  const opacity = fadeIn ? interpolate(frame, [0, fadeIn], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 1;
  const lighting = direction?.lighting?.change || "none";
  const flicker = lighting === "subtle_flicker" ? 0.025 * Math.sin(frame * 0.72) : 0;
  const exposure = lighting === "exposure_ramp" ? interpolate(progress, [0, 1], [0.035, -0.02]) : 0;
  const atmosphere = direction?.atmosphere?.effect || "none";
  const strength = clamp(direction?.atmosphere?.intensity ?? 0, 0, 1);
  const particleCount = atmosphere === "rain" ? 24 : ["dust", "embers", "particles"].includes(atmosphere) ? 16 : 0;

  return <AbsoluteFill style={{ opacity, overflow: "hidden", background: "#0b111a" }}>
    {scene.visualMode === "video" && scene.asset ? <OffthreadVideo src={staticFile(scene.asset)} muted style={mediaStyle} /> :
      scene.visualMode === "image" && scene.asset ? <Img src={staticFile(scene.asset)} style={mediaStyle} /> :
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 70% 30%, #33485d 0%, #172330 36%, #090e15 78%)" }}>
        <div style={{ position: "absolute", width: 680, height: 680, borderRadius: "50%", border: `1px solid ${accent}66`, right: -290 + Math.sin(frame / 32) * 18, top: 190, boxShadow: `0 0 100px ${accent}22, inset 0 0 100px ${accent}12` }} />
        <div style={{ position: "absolute", width: 430, height: 430, borderRadius: "50%", border: `1px solid ${accent}55`, right: -165, top: 315, transform: `rotate(${frame * 0.2}deg)` }} />
      </AbsoluteFill>}
    {atmosphere === "fog" ? <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 70%, #dce8f0${Math.round(16 * strength).toString(16).padStart(2, "0")}, transparent 72%)`, opacity: 0.5 }} /> : null}
    {particleCount > 0 ? <AbsoluteFill style={{ pointerEvents: "none", opacity: strength * 0.72 }}>
      {Array.from({ length: particleCount }, (_, i) => {
        const left = (i * 67 + 13) % width;
        const top = (i * 113 + frame * (atmosphere === "rain" ? 12 : 0.9 + (i % 3) * 0.25)) % height;
        const size = 2 + (i % 3);
        return <div key={i} style={{ position: "absolute", left, top, width: atmosphere === "rain" ? 2 : size, height: atmosphere === "rain" ? 28 : size, borderRadius: 99, background: atmosphere === "embers" ? "#ffb45e" : "#ffffff", boxShadow: atmosphere === "embers" ? "0 0 10px #ff8b38" : "none", opacity: 0.25 + (i % 4) * 0.12 }} />;
      })}
    </AbsoluteFill> : null}
    {lighting === "light_sweep" ? <div style={{ position: "absolute", top: "-20%", bottom: "-20%", width: "45%", background: "linear-gradient(90deg, transparent, #ffffff30, transparent)", transform: `translateX(${interpolate(frame, [0, duration], [-width, width * 2])}px) skewX(-18deg)`, mixBlendMode: "screen" }} /> : null}
    {lighting === "subtle_flicker" || lighting === "exposure_ramp" ? <AbsoluteFill style={{ background: "#ffffff", opacity: clamp(0.012 + flicker + exposure, 0, 0.06) }} /> : null}
    <AbsoluteFill style={{ background: "linear-gradient(180deg, #05080b44 0%, transparent 30%, #05080b66 100%)" }} />
  </AbsoluteFill>;
};

export const NexusVideo: React.FC<NexusVideoProps> = (props) => {
  const { fps } = useVideoConfig();
  let cursor = 0;
  const layers = props.scenes.map((scene, index) => {
    const sceneFrames = Math.max(1, Math.round(scene.durationSeconds * fps));
    const requestedOverlap = scene.sceneDirection?.transition?.in === "crossfade" ? clamp(scene.sceneDirection.transition.durationFrames || 8, 1, 12) : 0;
    const overlap = index === 0 ? 0 : Math.min(requestedOverlap, Math.max(0, sceneFrames - 1));
    const from = Math.max(0, cursor - overlap);
    const duration = sceneFrames + overlap;
    cursor += sceneFrames;
    return { scene, from, duration, overlapFrames: overlap };
  });
  return <AbsoluteFill style={{ backgroundColor: "#080d14", fontFamily: "Arial, Helvetica, sans-serif" }}>
    {layers.map((layer) => <Sequence key={layer.scene.id} from={layer.from} durationInFrames={layer.duration} layout="none">
      <SceneLayer scene={layer.scene} duration={layer.duration} overlapFrames={layer.overlapFrames} />
    </Sequence>)}
    {props.narrationAudio ? <Audio src={staticFile(props.narrationAudio)} /> : null}
    {props.musicAudio ? <Audio src={staticFile(props.musicAudio)} volume={0.12} /> : null}
  </AbsoluteFill>;
};
