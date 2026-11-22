import React from "react";
import { Composition } from "remotion";
import { Launch, timeline } from "./Launch";

export const Root: React.FC = () => (
  <Composition id="Launch" component={Launch} durationInFrames={Math.ceil(timeline().total)} fps={60} width={1920} height={1080} />
);
