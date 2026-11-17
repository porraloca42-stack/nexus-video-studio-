import React from "react";
import { AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { CaptionEvent, NexusScene, NexusVideoProps } from "./types";

const clamp = (value: number, min: number, max: number) => Math.max(min, Math.min(max, value));
const mod = (value: number, divisor: number) => ((value % divisor) + divisor) % divisor;

const keyLightPosition = (direction: string) => {
  const value = (direction || "").toLowerCase();
  if (value.includes("left") || value.includes("esquerda")) return "18% 42%";
  if (value.includes("right") || value.includes("direita")) return "82% 42%";
  if (value.includes("top") || value.includes("above") || value.includes("alto") || value.includes("cima")) return "50% 8%";
  if (value.includes("back") || value.includes("behind") || value.includes("contra")) return "50% 18%";
  return "50% 45%";
};

const moodFilter = (mood: string) => {
  const value = (mood || "").toLowerCase();
  if (/warm|golden|sunset|quente|dourad/.test(value)) return "saturate(1.07) sepia(0.035)";
  if (/cool|cold|moon|night|blue|frio|azul|noturn/.test(value)) return "saturate(0.91) hue-rotate(4deg)";
  if (/dramatic|high contrast|dram[aá]tic|contraste/.test(value)) return "contrast(1.055) saturate(0.94)";
  return "none";
};

const SceneLayer: React.FC<{ scene: NexusScene; duration: number; overlapFrames: number }> = ({ scene, duration, overlapFrames }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const accent = scene.accent || "#e8b66b";
  const isGeneratedVideo = scene.visualMode === "video";
  const isStill = !isGeneratedVideo;
  const direction = scene.sceneDirection;
  const camera = direction?.camera;
  const progress = clamp(frame / Math.max(1, duration - overlapFrames), 0, 1);
  const move = camera?.move || scene.cameraMotion || "static";
  const intensity = clamp(camera?.intensity ?? 0.45, 0, 1);

  // Still-image motion is explicit and restrained. Generated footage is passed through.
  const defaultStart = move === "pull_out" ? 1.08 : move === "static" ? 1 : 1.06;
  const defaultEnd = move === "push_in" ? 1.08 : move === "pull_out" ? 1 : move === "static" ? 1 : 1.06;
  const startScale = clamp(camera?.startScale ?? defaultStart, 1, 1.18);
  const endScale = clamp(camera?.endScale ?? defaultEnd, 1, 1.18);
  const scale = move === "static" ? 1 : interpolate(progress, [0, 1], [startScale, endScale]);
  const travel = 42 * intensity;
  const x = move === "pan_left" ? progress * travel : move === "pan_right" ? -progress * travel : 0;
  const y = move === "tilt_up" ? progress * travel : move === "tilt_down" ? -progress * travel : 0;
  const transform = "translate3d(" + x + "px, " + y + "px, 0) scale(" + scale + ")";
  const mediaStyle: React.CSSProperties = {
    width: "100%",
    height: "100%",
    objectFit: "cover",
    transform: isGeneratedVideo || move === "static" ? "none" : transform,
    transformOrigin: camera?.focus === "foreground" ? "50% 75%" : camera?.focus === "background" ? "50% 25%" : "50% 50%",
    filter: isStill ? moodFilter(direction?.lighting?.mood || "") : "none",
    willChange: isStill && move !== "static" ? "transform" : "auto",
  };

  const transitionFrames = clamp(direction?.transition?.durationFrames || overlapFrames || 8, 1, 12);
  const transitionIn = direction?.transition?.in || "cut";
  const transitionOut = direction?.transition?.out || "cut";
  const fadeIn = transitionIn === "crossfade" || transitionIn === "fade" || overlapFrames > 0 ? transitionFrames : 0;
  // Crossfades are handled by the incoming layer; fading both layers creates an unwanted dip.
  const fadeOut = transitionOut === "fade" ? transitionFrames : 0;
  const fadeInOpacity = fadeIn ? interpolate(frame, [0, fadeIn], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 1;
  const fadeOutOpacity = fadeOut ? interpolate(frame, [duration - fadeOut, duration], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 1;
  const opacity = Math.min(fadeInOpacity, fadeOutOpacity);

  // Lighting and atmosphere are restrained finishing treatments for stills only.
  // Never cover generated footage with synthetic particles, sweeps or fake fog.
  const lighting = isStill ? (direction?.lighting?.change || "none") : "none";
  const atmosphere = isStill ? (direction?.atmosphere?.effect || "none") : "none";
  const strength = clamp(direction?.atmosphere?.intensity ?? 0, 0, 0.35);
  const lightPosition = keyLightPosition(direction?.lighting?.keyDirection || "");
  const fogX = 48 + Math.sin(frame / 95) * 5;
  const fogY = 66 + Math.cos(frame / 120) * 3;
  const particleCount = atmosphere === "rain" ? 18 : atmosphere === "embers" ? 8 : atmosphere === "dust" || atmosphere === "particles" ? 10 : 0;

  return <AbsoluteFill style={{ opacity, overflow: "hidden", background: "#0b111a" }}>
    {scene.visualMode === "video" && scene.asset ? <OffthreadVideo src={staticFile(scene.asset)} muted style={mediaStyle} /> :
      scene.visualMode === "image" && scene.asset ? <Img src={staticFile(scene.asset)} style={mediaStyle} /> :
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 70% 30%, #33485d 0%, #172330 36%, #090e15 78%)" }}>
        <div style={{ position: "absolute", width: 680, height: 680, borderRadius: "50%", border: "1px solid " + accent + "44", right: -290 + Math.sin(frame / 32) * 8, top: 190, boxShadow: "0 0 80px " + accent + "18, inset 0 0 80px " + accent + "0d" }} />
        <div style={{ position: "absolute", width: 430, height: 430, borderRadius: "50%", border: "1px solid " + accent + "33", right: -165, top: 315, transform: "rotate(" + frame * 0.08 + "deg)" }} />
      </AbsoluteFill>}

    {isStill && lighting === "light_sweep" ? <AbsoluteFill style={{
      pointerEvents: "none",
      background: "radial-gradient(ellipse at " + lightPosition + ", rgba(255,244,220,0.16) 0%, rgba(255,244,220,0.055) 24%, transparent 62%)",
      mixBlendMode: "screen",
    }} /> : null}
    {isStill && lighting === "exposure_ramp" ? <AbsoluteFill style={{
      pointerEvents: "none",
      background: "#fff4df",
      opacity: interpolate(progress, [0, 1], [0.035, 0.005]),
      mixBlendMode: "soft-light",
    }} /> : null}
    {isStill && lighting === "subtle_flicker" ? <AbsoluteFill style={{
      pointerEvents: "none",
      background: "#fff4df",
      opacity: 0.008 + Math.sin(frame * 0.42) * 0.004,
      mixBlendMode: "screen",
    }} /> : null}

    {isStill && atmosphere === "fog" && strength > 0 ? <AbsoluteFill style={{
      pointerEvents: "none",
      background: "radial-gradient(ellipse at " + fogX + "% " + fogY + "%, rgba(220,232,240," + strength * 0.42 + ") 0%, rgba(220,232,240," + strength * 0.12 + ") 28%, transparent 68%)",
      mixBlendMode: "screen",
    }} /> : null}
    {isStill && particleCount > 0 && strength > 0 ? <AbsoluteFill style={{ pointerEvents: "none", opacity: strength * 1.35 }}>
      {Array.from({ length: particleCount }, (_, i) => {
        const seedX = mod(i * 83 + 19, width);
        const seedY = mod(i * 137 + 31, height);
        const rain = atmosphere === "rain";
        const ember = atmosphere === "embers";
        const size = rain ? 1.5 : ember ? 3 + (i % 2) : 1.5 + (i % 2);
        const left = rain ? mod(seedX - frame * (0.55 + (i % 3) * 0.12), width) : seedX + Math.sin(frame / (38 + i * 3) + i) * (ember ? 9 : 5);
        const top = rain ? mod(seedY + frame * (5.5 + (i % 4) * 0.7), height) : ember ? mod(seedY - frame * (0.7 + (i % 3) * 0.18), height) : mod(seedY + Math.sin(frame / (45 + i * 4) + i) * 16 - frame * 0.12, height);
        return <div key={i} style={{
          position: "absolute",
          left,
          top,
          width: size,
          height: rain ? 22 + (i % 3) * 5 : size,
          borderRadius: 99,
          background: ember ? "#ffb45e" : "#ffffff",
          boxShadow: ember ? "0 0 9px #ff8b38" : rain ? "0 0 3px #d9ecff" : "0 0 4px #ffffff",
          opacity: rain ? 0.2 + (i % 3) * 0.07 : ember ? 0.24 + (i % 3) * 0.08 : 0.16 + (i % 3) * 0.05,
          filter: ember ? "blur(0.4px)" : "none",
        }} />;
      })}
    </AbsoluteFill> : null}
    {isStill ? <AbsoluteFill style={{
      pointerEvents: "none",
      background: "radial-gradient(ellipse at 50% 46%, transparent 48%, rgba(0,0,0,0.18) 100%)",
    }} /> : null}
  </AbsoluteFill>;
};

const CaptionOverlay: React.FC<{ event: CaptionEvent }> = ({ event }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentSeconds = event.startSeconds + frame / fps;
  const position = event.position || "bottom";
  const justifyContent = position === "top" ? "flex-start" : position === "center" ? "center" : "flex-end";
  const words = event.words || [];
  return <AbsoluteFill style={{
    justifyContent,
    alignItems: "center",
    paddingTop: position === "top" ? 150 : 40,
    paddingBottom: position === "bottom" ? 190 : 40,
    paddingLeft: 54,
    paddingRight: 54,
    pointerEvents: "none",
  }}>
    <div style={{
      maxWidth: "100%",
      padding: "12px 20px",
      borderRadius: 16,
      background: "rgba(0, 0, 0, 0.58)",
      color: "#ffffff",
      fontSize: 46,
      fontWeight: 800,
      lineHeight: 1.18,
      textAlign: "center",
      textShadow: "0 3px 12px rgba(0,0,0,0.85)",
      overflowWrap: "anywhere",
    }}>
      {words.length ? words.map((word, index) => {
        const active = currentSeconds >= word.startSeconds && currentSeconds < word.endSeconds;
        const highlighted = Boolean(word.emphasis) || active;
        return <span key={index} style={{
          display: "inline-block",
          marginRight: 11,
          color: highlighted ? "#ffd477" : "#ffffff",
          transform: active ? "scale(1.035)" : "scale(1)",
        }}>{word.text}</span>;
      }) : event.text}
    </div>
  </AbsoluteFill>;
};

export const NexusVideo: React.FC<NexusVideoProps> = (props) => {
  const { fps } = useVideoConfig();
  let cursor = 0;
  const layers = props.scenes.map((scene, index) => {
    const sceneFrames = Math.max(1, Math.round(scene.durationSeconds * fps));
    const previousScene = props.scenes[index - 1];
    const incoming = scene.sceneDirection?.transition?.in === "crossfade";
    const previousOutgoing = previousScene?.sceneDirection?.transition?.out === "crossfade";
    const requestedOverlap = incoming || previousOutgoing
      ? Math.max(scene.sceneDirection?.transition?.durationFrames || 0, previousScene?.sceneDirection?.transition?.durationFrames || 0, 8)
      : 0;
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
    {props.musicAudio ? <Audio
      src={staticFile(props.musicAudio)}
      volume={(frame) => {
        const seconds = frame / fps;
        const activeMix = (props.audioMixEvents || []).filter(
          (event) => seconds >= event.startSeconds && seconds < event.endSeconds
        );
        const baseVolume = clamp(props.musicVolume ?? 0.12, 0, 1);
        if (!activeMix.length) return baseVolume;
        const duckedVolumes = activeMix.map((event) => {
          const fadeIn = event.fadeInSeconds ?? 0.12;
          const fadeOut = event.fadeOutSeconds ?? 0.12;
          const fadeInProgress = fadeIn > 0
            ? clamp((seconds - event.startSeconds) / fadeIn, 0, 1)
            : 1;
          const fadeOutProgress = fadeOut > 0
            ? clamp((event.endSeconds - seconds) / fadeOut, 0, 1)
            : 1;
          const envelope = Math.min(fadeInProgress, fadeOutProgress);
          return baseVolume + (event.musicVolume - baseVolume) * envelope;
        });
        return clamp(Math.min(...duckedVolumes), 0, 1);
      }}
    /> : null}
    {(props.soundEffects || []).map((event) => (
      <Sequence
        key={event.id}
        from={Math.max(0, Math.round(event.startSeconds * fps))}
        durationInFrames={Math.max(1, Math.round(event.durationSeconds * fps))}
        layout="none"
      >
        <Audio src={staticFile(event.asset)} volume={clamp(event.volume, 0, 1)} />
      </Sequence>
    ))}
    {(props.captionEvents || []).map((event) => (
      <Sequence
        key={event.id}
        from={Math.max(0, Math.round(event.startSeconds * fps))}
        durationInFrames={Math.max(1, Math.round((event.endSeconds - event.startSeconds) * fps))}
        layout="none"
      >
        <CaptionOverlay event={event} />
      </Sequence>
    ))}
  </AbsoluteFill>;
};
