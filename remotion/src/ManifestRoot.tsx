import React from "react";
import { Composition } from "remotion";
import { NexusVideo } from "./NexusVideo";
import type { NexusVideoProps } from "./types";

const defaultProps: NexusVideoProps = {
  width: 720,
  height: 1280,
  fps: 30,
  durationInFrames: 1500,
  title: "NEXUS Manifest",
  scenes: [
    { id: "scene-1", durationSeconds: 25, narration: "A mudança começa com uma escolha.", visualMode: "graphic", headline: "Toda mudança\ncomeça por uma escolha." },
    { id: "scene-2", durationSeconds: 25, narration: "Transforme intenção em atitude.", visualMode: "graphic", headline: "Transforme intenção\nem atitude.", accent: "#7cc9d4" }
  ],
  captions: [
    { text: "Toda mudança começa com uma escolha.", startFrame: 0, endFrame: 375 },
    { text: "Transforme intenção em atitude.", startFrame: 750, endFrame: 1125 }
  ]
};

export const ManifestRoot: React.FC = () => (
  <Composition
    id="NexusFromManifest"
    component={NexusVideo}
    width={720}
    height={1280}
    fps={30}
    durationInFrames={1500}
    defaultProps={defaultProps}
    calculateMetadata={({ props }) => ({
      width: props.width,
      height: props.height,
      fps: props.fps,
      durationInFrames: props.durationInFrames,
    })}
  />
);
