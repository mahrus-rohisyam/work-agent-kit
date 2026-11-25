import React from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { z } from "zod";
import { FPS, Spec, spec as featureSpec } from "./spec";
import { useBrand } from "./brand";
import { Clip, EndCard } from "./parts";

// A product tour: several short scenes, one selling point each, then the end card.
// Each scene: a title (the selling point) above the footage and a short caption below it.

const clipSchema = featureSpec.shape.clip;

export const showcaseSpec = z.object({
  brand: z.string().default("example"),
  theme: z.enum(["dark", "light"]).default("dark"),
  scenes: z.array(z.object({
    title: z.string(),
    caption: z.string().default(""),
    clip: clipSchema,
  })).min(1),
  cta: z.string().default(""),
  showTagline: z.boolean().default(true),
  endCardSec: z.number().default(3),
  music: z.string().optional(),
  musicVolume: z.number().default(0.35),
});
export type ShowcaseSpec = z.infer<typeof showcaseSpec>;

const sceneFrames = (c: ShowcaseSpec["scenes"][number]["clip"]) =>
  Math.round(((c.endSec - c.startSec) / c.playbackRate) * FPS);
export const showcaseFrames = (s: ShowcaseSpec) =>
  s.scenes.reduce((n, sc) => n + sceneFrames(sc.clip), 0) + Math.round(s.endCardSec * FPS);

const ease = Easing.bezier(0.16, 1, 0.3, 1);

/** Text that rises into place at the start of its scene. *word* is drawn in the accent color. */
const Line: React.FC<{ text: string; size: number; weight: number; color: string; highlight: string; delay?: number }> = ({ text, size, weight, color, highlight, delay = 0 }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [delay, delay + 0.25 * FPS], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
  const parts = text.split(/(\*[^*]+\*)/g).filter(Boolean);
  return (
    <div style={{ fontSize: size, fontWeight: weight, color, lineHeight: 1.1, letterSpacing: "-0.025em", textAlign: "center", opacity: p, transform: `translateY(${(1 - p) * 18}px)`, textWrap: "balance" }}>
      {parts.map((s, i) => s.startsWith("*") ? <span key={i} style={{ color: highlight }}>{s.slice(1, -1)}</span> : <span key={i}>{s}</span>)}
    </div>
  );
};

/** One node per scene, joined by a line. Nodes already shown use the accent color, the current one the brand color. */
const Progress: React.FC<{ count: number; index: number; brand: string; accent: string; border: string; size: number }> = ({ count, index, brand, accent, border, size }) => {
  const gap = size * 2.2;
  return (
    <div style={{ display: "flex", alignItems: "center" }}>
      {Array.from({ length: count }).map((_, i) => (
        <React.Fragment key={i}>
          {i > 0 && <div style={{ width: gap, height: size * 0.28, background: i <= index ? accent : border }} />}
          <div style={{ width: size, height: size, borderRadius: "50%", background: i < index ? accent : i === index ? brand : border }} />
        </React.Fragment>
      ))}
    </div>
  );
};

const Music: React.FC<{ s: ShowcaseSpec }> = ({ s }) => {
  const { durationInFrames } = useVideoConfig();
  if (!s.music) return null;
  return <Audio src={staticFile(s.music)} loop volume={(f) => interpolate(f, [0, 15, durationInFrames - 30, durationInFrames], [0, s.musicVolume, s.musicVolume, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />;
};

type Layout = {
  title: React.CSSProperties; titleSize: number;
  clip: React.CSSProperties;
  caption: React.CSSProperties; captionSize: number;
  progress: React.CSSProperties; node: number;
  radius: number; endScale: number;
};

const LAYOUTS: Record<"vertical" | "landscape", Layout> = {
  // 1080×1920. Text stays out of the top 150 px, bottom 420 px and right 140 px (TikTok UI).
  vertical: {
    progress: { top: 170, left: 60, right: 140, height: 40 }, node: 22,
    title: { top: 230, left: 60, right: 140, height: 250 }, titleSize: 76,
    clip: { top: 510, left: 40, right: 40, height: 800 },
    caption: { top: 1340, left: 60, right: 140, height: 150 }, captionSize: 58,
    radius: 24, endScale: 1,
  },
  // 1920×1080 for LinkedIn, YouTube and the landing page.
  landscape: {
    progress: { top: 44, left: 0, right: 0, height: 30 }, node: 16,
    title: { top: 84, left: 160, right: 160, height: 110 }, titleSize: 60,
    clip: { top: 214, left: 260, right: 260, height: 740 },
    caption: { top: 970, left: 160, right: 160, height: 80 }, captionSize: 40,
    radius: 16, endScale: 0.9,
  },
};

const box = (s: React.CSSProperties): React.CSSProperties => ({ position: "absolute", display: "flex", alignItems: "center", justifyContent: "center", ...s });

const Showcase: React.FC<ShowcaseSpec & { layout: "vertical" | "landscape" }> = (props) => {
  const s = showcaseSpec.parse(props);
  const L = LAYOUTS[props.layout];
  const b = useBrand(s.brand, s.theme);
  let from = 0;
  return (
    <AbsoluteFill style={{ background: b.c.bg, fontFamily: b.font }}>
      {s.scenes.map((sc, i) => {
        const dur = sceneFrames(sc.clip);
        const start = from;
        from += dur;
        return (
          <Sequence key={i} from={start} durationInFrames={dur}>
            <SceneFade>
              <div style={box(L.progress)}>
                <Progress count={s.scenes.length} index={i} brand={b.c.brand} accent={b.c.accent} border={b.c.border} size={L.node} />
              </div>
              <div style={box(L.title)}>
                <Line text={sc.title} size={L.titleSize} weight={800} color={b.c.text} highlight={b.c.accent} />
              </div>
              <div style={{ position: "absolute", ...L.clip }}>
                <Clip spec={{ clip: sc.clip } as Spec} radius={L.radius} border={b.c.border} />
              </div>
              {sc.caption && (
                <div style={box(L.caption)}>
                  <Line text={sc.caption} size={L.captionSize} weight={700} color={b.c.subtle} highlight={b.c.accent} delay={0.35 * FPS} />
                </div>
              )}
            </SceneFade>
          </Sequence>
        );
      })}
      <Sequence from={from}>
        <EndCard spec={{ brand: s.brand, theme: s.theme, cta: s.cta, showTagline: s.showTagline } as Spec} scale={L.endScale} />
      </Sequence>
      <Music s={s} />
    </AbsoluteFill>
  );
};

/** Short fade in from the background at the start of each scene. */
const SceneFade: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

export const ShowcaseVertical: React.FC<ShowcaseSpec> = (p) => <Showcase {...p} layout="vertical" />;
export const ShowcaseLandscape: React.FC<ShowcaseSpec> = (p) => <Showcase {...p} layout="landscape" />;
