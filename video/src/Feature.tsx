import React from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { FPS, Spec, clipSeconds } from "./spec";
import { useBrand } from "./brand";
import { Captions, Clip, EndCard, Hook } from "./parts";

const Music: React.FC<{ spec: Spec }> = ({ spec }) => {
  const { durationInFrames } = useVideoConfig();
  if (!spec.music) return null;
  return (
    <Audio
      src={staticFile(spec.music)}
      loop
      volume={(f) => interpolate(f, [0, 15, durationInFrames - 30, durationInFrames], [0, spec.musicVolume, spec.musicVolume, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}
    />
  );
};

/**
 * 9:16 (TikTok, Reels, Shorts). Safe area: text stays out of the top 150 px,
 * the bottom 420 px and the right 140 px, where the platform UI sits.
 */
export const FeatureVertical: React.FC<Spec> = (spec) => {
  const b = useBrand(spec.brand, spec.theme);
  const clipFrames = Math.round(clipSeconds(spec) * FPS);
  return (
    <AbsoluteFill style={{ background: b.c.bg, fontFamily: b.font }}>
      <Sequence durationInFrames={clipFrames}>
        <AbsoluteFill>
          <div style={{ position: "absolute", top: 170, left: 60, right: 140, height: 300, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Hook text={spec.hook} size={84} color={b.c.text} />
          </div>
          <div style={{ position: "absolute", top: 500, left: 40, right: 40, height: 820 }}>
            <Clip spec={spec} radius={b.t.radius.lg * 3} border={b.c.border} />
          </div>
          <div style={{ position: "absolute", top: 1350, left: 60, right: 140, height: 150, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Captions spec={spec} size={60} color={b.c.text} highlight={b.c.accent} />
          </div>
        </AbsoluteFill>
      </Sequence>
      <Sequence from={clipFrames}>
        <EndCard spec={spec} scale={1} />
      </Sequence>
      <Music spec={spec} />
    </AbsoluteFill>
  );
};

/** 16:9 for the landing page (and YouTube/LinkedIn). Captions optional. */
export const FeatureLandscape: React.FC<Spec> = (spec) => {
  const b = useBrand(spec.brand, spec.theme);
  const frame = useCurrentFrame();
  const clipFrames = Math.round(clipSeconds(spec) * FPS);
  const hookOut = interpolate(frame, [2.2 * FPS, 2.6 * FPS], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const hasCaptions = spec.captions.length > 0;
  return (
    <AbsoluteFill style={{ background: b.c.bg, fontFamily: b.font }}>
      <Sequence durationInFrames={clipFrames}>
        <AbsoluteFill>
          <div style={{ position: "absolute", left: 120, right: 120, top: 60, bottom: hasCaptions ? 200 : 60 }}>
            <Clip spec={spec} radius={b.t.radius.lg * 2} border={b.c.border} />
          </div>
          {spec.hook && (
            <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: hookOut, background: `${b.c.bg}E6` }}>
              <div style={{ maxWidth: 1300 }}><Hook text={spec.hook} size={96} color={b.c.text} /></div>
            </AbsoluteFill>
          )}
          {hasCaptions && (
            <div style={{ position: "absolute", left: 160, right: 160, bottom: 50, height: 120, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Captions spec={spec} size={52} color={b.c.text} highlight={b.c.accent} />
            </div>
          )}
        </AbsoluteFill>
      </Sequence>
      <Sequence from={clipFrames}>
        <EndCard spec={spec} scale={0.9} />
      </Sequence>
      <Music spec={spec} />
    </AbsoluteFill>
  );
};

/** 1:1 for LinkedIn / X / Instagram feed. */
export const FeatureSquare: React.FC<Spec> = (spec) => {
  const b = useBrand(spec.brand, spec.theme);
  const clipFrames = Math.round(clipSeconds(spec) * FPS);
  return (
    <AbsoluteFill style={{ background: b.c.bg, fontFamily: b.font }}>
      <Sequence durationInFrames={clipFrames}>
        <AbsoluteFill>
          <div style={{ position: "absolute", top: 50, left: 60, right: 60, height: 190, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Hook text={spec.hook} size={64} color={b.c.text} />
          </div>
          <div style={{ position: "absolute", top: 260, left: 40, right: 40, height: 620 }}>
            <Clip spec={spec} radius={b.t.radius.lg * 2} border={b.c.border} />
          </div>
          <div style={{ position: "absolute", bottom: 40, left: 60, right: 60, height: 140, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Captions spec={spec} size={48} color={b.c.text} highlight={b.c.accent} />
          </div>
        </AbsoluteFill>
      </Sequence>
      <Sequence from={clipFrames}>
        <EndCard spec={spec} scale={0.8} />
      </Sequence>
      <Music spec={spec} />
    </AbsoluteFill>
  );
};
