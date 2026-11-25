import React from "react";
import {
  AbsoluteFill, Img, OffthreadVideo, Easing, interpolate, staticFile,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import { FPS, Spec, focusKey } from "./spec";
import { z } from "zod";
import { useBrand } from "./brand";

const ease = Easing.bezier(0.16, 1, 0.3, 1); // calm ease-out, no overshoot

type Focus = z.infer<typeof focusKey>;

/** Interpolate the focus keyframes (x, y, zoom) at time t seconds. */
export const focusAt = (keys: Focus[], t: number): Omit<Focus, "at"> => {
  if (keys.length === 0) return { x: 0.5, y: 0.5, zoom: 1 };
  const ks = [...keys].sort((a, b) => a.at - b.at);
  const times = ks.map((k) => k.at);
  if (ks.length === 1) return ks[0];
  const opt = { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) } as const;
  // interpolate needs at least 2 points; it eases within each segment.
  return {
    x: interpolate(t, times, ks.map((k) => k.x), opt),
    y: interpolate(t, times, ks.map((k) => k.y), opt),
    zoom: interpolate(t, times, ks.map((k) => k.zoom), opt),
  };
};

/** The product footage, cropped to its box and following the focus keyframes. */
export const Clip: React.FC<{ spec: Spec; radius: number; border: string }> = ({ spec, radius, border }) => {
  const frame = useCurrentFrame();
  const t = (frame / FPS) * spec.clip.playbackRate;
  const f = focusAt(spec.clip.focus, t);
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", borderRadius: radius, border: `2px solid ${border}` }}>
      <OffthreadVideo
        src={staticFile(spec.clip.src)}
        startFrom={Math.round(spec.clip.startSec * FPS)}
        endAt={Math.round(spec.clip.endSec * FPS)}
        playbackRate={spec.clip.playbackRate}
        muted
        style={{
          width: "100%", height: "100%", objectFit: "cover",
          objectPosition: `${f.x * 100}% ${f.y * 100}%`,
          transform: `scale(${f.zoom})`,
          transformOrigin: `${f.x * 100}% ${f.y * 100}%`,
        }}
      />
    </div>
  );
};

/** One caption chunk at a time, fading up into place over 150 ms. */
export const Captions: React.FC<{ spec: Spec; size: number; color: string; highlight: string }> = ({ spec, size, color, highlight }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const cur = spec.captions.find((c) => t >= c.from && t < c.to);
  if (!cur) return null;
  const local = frame - cur.from * FPS;
  const p = interpolate(local, [0, 0.15 * FPS], [0, 1], { extrapolateRight: "clamp", easing: ease });
  // *word* in the caption text marks the word to highlight in the accent color.
  const parts = cur.text.split(/(\*[^*]+\*)/g).filter(Boolean);
  return (
    <div style={{
      fontSize: size, fontWeight: 700, lineHeight: 1.15, color, textAlign: "center",
      letterSpacing: "-0.02em", opacity: p, transform: `translateY(${(1 - p) * 16}px)`,
      textWrap: "balance",
    }}>
      {parts.map((s, i) => s.startsWith("*")
        ? <span key={i} style={{ color: highlight }}>{s.slice(1, -1)}</span>
        : <span key={i}>{s}</span>)}
    </div>
  );
};

/** Closing card: logo, the one next step, and the tagline. */
export const EndCard: React.FC<{ spec: Spec; scale: number }> = ({ spec, scale }) => {
  const frame = useCurrentFrame();
  const b = useBrand(spec.brand, spec.theme);
  const step = (i: number) => interpolate(frame, [i * 6, i * 6 + 9], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const rise = (i: number) => ({ opacity: step(i), transform: `translateY(${(1 - step(i)) * 20 * scale}px)` });
  return (
    <AbsoluteFill style={{ background: b.c.bg, alignItems: "center", justifyContent: "center", fontFamily: b.font, gap: 36 * scale }}>
      <Img src={b.logo} style={{ height: 120 * scale, ...rise(0) }} />
      {spec.cta && (
        <div style={{ ...rise(1), fontSize: 64 * scale, fontWeight: 700, color: b.c.text, textAlign: "center", maxWidth: "80%", letterSpacing: "-0.02em", textWrap: "balance" }}>
          {spec.cta}
        </div>
      )}
      {spec.showTagline && (
        <div style={{ ...rise(2), fontSize: 34 * scale, color: b.c.subtle, fontWeight: 500 }}>{b.t.tagline}</div>
      )}
    </AbsoluteFill>
  );
};

/** Short hook text shown over the first seconds. */
export const Hook: React.FC<{ text: string; size: number; color: string }> = ({ text, size, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = interpolate(frame, [0, 0.2 * fps], [0, 1], { extrapolateRight: "clamp", easing: ease });
  return (
    <div style={{ fontSize: size, fontWeight: 800, color, lineHeight: 1.08, letterSpacing: "-0.03em", textAlign: "center", opacity: p, transform: `translateY(${(1 - p) * 20}px)`, textWrap: "balance" }}>
      {text}
    </div>
  );
};
