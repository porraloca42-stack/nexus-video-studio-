export type NexusScene = {
  id: string;
  durationSeconds: number;
  narration: string;
  visualMode: "graphic" | "image" | "video";
  asset?: string;
  headline?: string;
  visualDescription?: string;
  accent?: string;
};

export type NexusCaption = {
  text: string;
  startFrame: number;
  endFrame: number;
};

export type NexusVideoProps = {
  width: number;
  height: number;
  fps: number;
  durationInFrames: number;
  title: string;
  narrationAudio?: string;
  musicAudio?: string;
  scenes: NexusScene[];
  captions: NexusCaption[];
};
