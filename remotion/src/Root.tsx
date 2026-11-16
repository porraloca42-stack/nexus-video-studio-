import React from "react";
import { Composition } from "remotion";
import { NexusDemo } from "./NexusDemo";
import { ManifestRoot } from "./ManifestRoot";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="NexusDemo"
        component={NexusDemo}
        durationInFrames={50 * 30}
        fps={30}
        width={720}
        height={1280}
      />
      <ManifestRoot />
    </>
  );
};
