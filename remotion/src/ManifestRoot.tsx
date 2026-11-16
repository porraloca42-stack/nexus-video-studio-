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
    { id: "scene-1", durationSeconds: 25, narration: "A mudança começa com uma escolha.", visualMode: "graphic" },
    { id: "scene-2", durationSeconds: 25, narration: "Transforme intenção em atitude.", visualMode: "graphic", accent: "#7cc9d4" }
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
