export type CameraMove = "push_in" | "pull_out" | "pan_left" | "pan_right" | "tilt_up" | "tilt_down" | "static";
export type SceneDirection = {
  camera: { move: CameraMove; intensity: number; startScale: number; endScale: number; focus: "subject" | "foreground" | "background" };
  depthLayers: { foreground: string; subject: string; background: string; parallaxStrength: number };
  lighting: { mood: string; keyDirection: string; change: "none" | "subtle_flicker" | "light_sweep" | "exposure_ramp" };
  atmosphere: { effect: "none" | "dust" | "rain" | "fog" | "embers" | "particles"; intensity: number };
  transition: { in: "cut" | "crossfade" | "match_cut" | "fade"; out: "cut" | "crossfade" | "match_cut" | "fade"; durationFrames: number };
  beats: Array<{ at: number; event: string; visualTarget: string }>;
};
export type CaptionWord = {
  text: string;
  startSeconds: number;
  endSeconds: number;
  emphasis?: boolean;
};
export type CaptionEvent = {
  id: string;
  startSeconds: number;
  endSeconds: number;
  text: string;
  position?: "top" | "center" | "bottom";
  words?: CaptionWord[];
};
export type SoundEffectEvent = {
  id: string;
  asset: string;
  startSeconds: number;
  durationSeconds: number;
  volume: number;
};
export type AudioMixEvent = {
  startSeconds: number;
  endSeconds: number;
  musicVolume: number;
  fadeInSeconds?: number;
  fadeOutSeconds?: number;
};
export type NexusScene = {
  id: string; durationSeconds: number; narration: string; visualMode: "graphic" | "image" | "video";
  asset?: string; imagePrompt?: string; cameraMotion?: CameraMove; motionEvents?: string[];
  sceneDirection?: SceneDirection; accent?: string;
};
export type NexusVideoProps = {
  width: number; height: number; fps: number; durationInFrames: number; title: string;
  narrationAudio?: string; musicAudio?: string; musicVolume?: number; scenes: NexusScene[];
  captionEvents?: CaptionEvent[]; soundEffects?: SoundEffectEvent[]; audioMixEvents?: AudioMixEvent[];
};
