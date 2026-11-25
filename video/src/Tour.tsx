import React from "react";
import {
  AbsoluteFill, Audio, Easing, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import { icons, type LucideIcon } from "lucide-react";
import { z } from "zod";
import { FPS, Spec, spec as featureSpec } from "./spec";
import { useBrand } from "./brand";
import { Clip } from "./parts";

// Business tour (16:9): what teams achieve with the product, not a click-through.
// One spec, a list of typed scenes. Copy lives in the JSON so slop_check can lint it.
// Icons are Lucide names in PascalCase (the set the product itself uses), e.g. "Headset".

const clip = featureSpec.shape.clip;
const media = z.object({
  image: z.string().optional().describe("still under video/public"),
  clip: clip.optional(),
  x: z.number().default(0.5), y: z.number().default(0.5), zoom: z.number().default(1),
  label: z.string().default("").describe("shown in the frame's title bar next to the brand mark"),
});

const scene = z.discriminatedUnion("kind", [
  z.object({
    kind: z.literal("opener"), sec: z.number(), title: z.string(), sub: z.string().default(""),
    wordAt: z.array(z.number()).default([]).describe("seconds at which each title word appears (synced to the voice)"),
  }),
  z.object({
    kind: z.literal("kinetic"), sec: z.number(), words: z.array(z.string()),
    everyBeats: z.number().default(2),
  }),
  z.object({
    kind: z.literal("hub"), sec: z.number(), title: z.string(),
    nodes: z.array(z.object({ label: z.string(), text: z.string(), icon: z.string() })),
  }),
  z.object({
    kind: z.literal("usecase"), sec: z.number(), eyebrow: z.string(), icon: z.string(), title: z.string(),
    steps: z.array(z.object({ text: z.string(), icon: z.string() })), media,
  }),
  z.object({
    kind: z.literal("portal"), sec: z.number(), title: z.string(),
    panes: z.array(z.object({ caption: z.string(), icon: z.string(), media })),
  }),
  z.object({
    kind: z.literal("chat"), sec: z.number(), title: z.string(), label: z.string(),
    prompt: z.string(), calls: z.array(z.object({ tool: z.string(), text: z.string() })),
    reply: z.string(), media, caption: z.string(), note: z.string().default(""),
  }),
  z.object({
    kind: z.literal("grid"), sec: z.number(), title: z.string(),
    items: z.array(z.object({ title: z.string(), text: z.string(), icon: z.string() })),
  }),
]);

export const tourSpec = z.object({
  brand: z.string().default("example"),
  theme: z.enum(["dark", "light"]).default("light"),
  scenes: z.array(scene).min(1),
  cta: z.string().default(""),
  showTagline: z.boolean().default(true),
  endCardSec: z.number().default(4),
  music: z.string().optional(),
  musicVolume: z.number().default(0.4),
  bpm: z.number().default(120),
  voice: z.array(z.object({ src: z.string(), at: z.number(), volume: z.number().default(1), duckTo: z.number().default(0.45), sec: z.number() })).default([]),
});
export type TourSpec = z.infer<typeof tourSpec>;
type Scene = z.infer<typeof scene>;
type Media = z.infer<typeof media>;

export const tourFrames = (s: TourSpec) =>
  s.scenes.reduce((n, sc) => n + Math.round(sc.sec * FPS), 0) + Math.round(s.endCardSec * FPS);

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const useIn = (at: number, dur = 0.4) => {
  const f = useCurrentFrame();
  return interpolate(f, [at * FPS, (at + dur) * FPS], [0, 1], { ...clamp, easing: ease });
};
const rise = (p: number, px = 24): React.CSSProperties => ({ opacity: p, transform: `translateY(${(1 - p) * px}px)` });

type B = ReturnType<typeof useBrand>;

const BpmCtx = React.createContext(120);
/** 1 on each beat (kick), decaying quickly; `every` beats between pulses. Frame is the scene's local frame. */
const usePulse = (every = 1, offsetFrames = 0) => {
  const f = useCurrentFrame() + offsetFrames;
  const bpm = React.useContext(BpmCtx);
  const period = (60 / bpm) * every * FPS;
  const phase = ((f % period) + period) % period;
  return Math.exp(-(phase / FPS) * 9);
};

const Icon: React.FC<{ name: string; size: number; color: string; stroke?: number }> = ({ name, size, color, stroke = 2 }) => {
  const C = (icons as Record<string, LucideIcon>)[name];
  if (!C) throw new Error(`Unknown Lucide icon "${name}"`);
  return <C size={size} color={color} strokeWidth={stroke} />;
};

/** An icon on a soft brand tile, the way the product shows feature icons. */
const IconTile: React.FC<{ name: string; b: B; size: number; filled?: boolean }> = ({ name, b, size, filled }) => (
  <div style={{ width: size, height: size, borderRadius: size * 0.26, background: filled ? b.c.brand : b.c.brandSubtle, display: "grid", placeItems: "center", flex: "none" }}>
    <Icon name={name} size={size * 0.52} color={filled ? b.c.onBrand : b.c.brand} />
  </div>
);

/** `*word*` in copy is drawn in the brand step-2 color. */
const Rich: React.FC<{ text: string; accent: string }> = ({ text, accent }) => (
  <>{text.split(/(\*[^*]+\*)/g).filter(Boolean).map((s, i) =>
    s.startsWith("*") ? <span key={i} style={{ color: accent }}>{s.slice(1, -1)}</span> : <span key={i}>{s}</span>)}</>
);

/** Words land one by one, on 8th notes by default, rising and settling with a short overshoot. */
const Words: React.FC<{ text: string; accent: string; at: number; step?: number; times?: number[] }> = ({ text, accent, at, step = 0.25, times }) => {
  const f = useCurrentFrame();
  const tokens = text.split(/(\s+)/);
  let wi = 0, hl = false;
  return (
    <>{tokens.map((tok, i) => {
      if (/^\s+$/.test(tok)) return <span key={i}>{tok}</span>;
      const open = tok.startsWith("*"), close = tok.endsWith("*");
      if (open) hl = true;
      const word = tok.replace(/\*/g, "");
      const t0 = times?.[wi] ?? at + wi * step;
      wi++;
      const p = interpolate(f, [t0 * FPS, (t0 + 0.28) * FPS], [0, 1], { ...clamp, easing: Easing.bezier(0.34, 1.4, 0.64, 1) });
      const el = (
        <span key={i} style={{ display: "inline-block", opacity: Math.min(1, p * 1.5), transform: `translateY(${(1 - p) * 40}px) scale(${0.9 + p * 0.1})`, color: hl ? accent : undefined }}>{word}</span>
      );
      if (close) hl = false;
      return el;
    })}</>
  );
};

const Title: React.FC<{ text: string; b: B; at?: number; size?: number; eyebrow?: string; icon?: string; align?: "center" | "left"; times?: number[] }> = ({ text, b, at = 0.1, size = 64, eyebrow, icon, align = "center", times }) => {
  const pe = useIn(at - 0.05, 0.4);
  return (
    <div style={{ textAlign: align }}>
      {eyebrow && (
        <div style={{ ...rise(pe, 12), display: "flex", alignItems: "center", gap: 14, marginBottom: 18, justifyContent: align === "center" ? "center" : "flex-start" }}>
          {icon && <IconTile name={icon} b={b} size={48} filled />}
          <span style={{ fontSize: 24, fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: b.c.brand }}>{eyebrow}</span>
        </div>
      )}
      <div style={{ fontSize: size, fontWeight: 800, lineHeight: 1.12, letterSpacing: "-0.03em", color: b.c.text, textWrap: "balance" }}>
        <Words text={text} accent={b.c.accent} at={at} times={times} />
      </div>
    </div>
  );
};

/** The brand mark, scaling into place. */
const BuildMark: React.FC<{ b: B; size: number; at?: number }> = ({ b, size, at = 0 }) => {
  const p = useIn(at, 0.5);
  return <Img src={b.mark} style={{ width: size, height: size, opacity: p, transform: `scale(${0.7 + 0.3 * p})` }} />;
};

/** Product footage in a frame whose title bar carries the brand mark, like an app window. */
const MediaBox: React.FC<{ m: Media; b: B; sec: number; radius?: number; bar?: number }> = ({ m, b, sec, radius = 18, bar = 52 }) => {
  const f = useCurrentFrame();
  const punch = usePulse(4);
  const z = m.zoom * interpolate(f, [0, Math.max(1, sec) * FPS], [1, 1.06], clamp) * (1 + 0.012 * punch);
  return (
    <div style={{ position: "absolute", inset: 0, borderRadius: radius, overflow: "hidden", border: `1.5px solid ${b.c.border}`, background: b.c.surface, boxShadow: "0 24px 60px rgba(30,27,75,.14), 0 4px 12px rgba(30,27,75,.06)" }}>
      <div style={{ height: bar, display: "flex", alignItems: "center", gap: 12, padding: "0 20px", borderBottom: `1.5px solid ${b.c.border}`, background: b.c.surface }}>
        <Img src={b.mark} style={{ height: bar * 0.56 }} />
        <span style={{ fontSize: bar * 0.4, fontWeight: 700, color: b.c.text }}>{b.t.name}</span>
        {m.label && <span style={{ fontSize: bar * 0.36, color: b.c.subtle }}>· {m.label}</span>}
      </div>
      <div style={{ position: "absolute", top: bar, left: 0, right: 0, bottom: 0, overflow: "hidden" }}>
        {m.clip ? (
          <Clip spec={{ clip: m.clip } as Spec} radius={0} border="transparent" />
        ) : m.image ? (
          <Img src={staticFile(m.image)} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: `${m.x * 100}% ${m.y * 100}%`, transform: `scale(${z})`, transformOrigin: `${m.x * 100}% ${m.y * 100}%` }} />
        ) : null}
      </div>
    </div>
  );
};

// ── Scenes ──────────────────────────────────────────────────────────────────

const Opener: React.FC<{ s: Extract<Scene, { kind: "opener" }>; b: B }> = ({ s, b }) => {
  const pw = useIn(0.75, 0.5);
  const ps = useIn(s.wordAt.length ? s.wordAt[s.wordAt.length - 1] + 0.3 : 1.5, 0.5);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 34, padding: "0 200px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 28 }}>
        <BuildMark b={b} size={150} at={0.1} />
        <div style={{ fontSize: 104, fontWeight: 800, letterSpacing: "-0.04em", lineHeight: 1, color: b.c.text, opacity: pw, transform: `translateX(${(1 - pw) * -24}px)` }}>{b.t.name}</div>
      </div>
      <Title text={s.title} b={b} size={76} at={1.1} times={s.wordAt.length ? s.wordAt : undefined} />
      {s.sub && <div style={{ ...rise(ps), fontSize: 34, color: b.c.subtle, fontWeight: 500, textAlign: "center", textWrap: "balance", maxWidth: 1300 }}>{s.sub}</div>}
    </AbsoluteFill>
  );
};

const Hub: React.FC<{ s: Extract<Scene, { kind: "hub" }>; b: B }> = ({ s, b }) => {
  const f = useCurrentFrame();
  const cx = 960, cy = 600, rx = 650, ry = 300;
  const n = s.nodes.length;
  const center = useIn(0.0, 0.35);
  const kick = usePulse(1);
  const pts = s.nodes.map((_, i) => {
    const a = -Math.PI / 2 + (i / n) * Math.PI * 2;
    return { x: cx + rx * Math.cos(a), y: cy + ry * Math.sin(a) };
  });
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 60, left: 160, right: 160 }}><Title text={s.title} b={b} size={60} /></div>
      <svg width={1920} height={1080} style={{ position: "absolute", inset: 0 }}>
        {pts.map((p, i) => {
          const start = (0.5 + i * 0.25) * FPS;
          const draw = interpolate(f, [start, start + 0.5 * FPS], [0, 1], { ...clamp, easing: ease });
          const len = Math.hypot(p.x - cx, p.y - cy);
          const period = 1.6 * FPS;
          const t = ((f - start - 0.5 * FPS + i * 7) % period) / period;
          const live = f > start + 0.5 * FPS;
          const dir = i % 2 === 0 ? t : 1 - t;
          const px = cx + (p.x - cx) * dir, py = cy + (p.y - cy) * dir;
          return (
            <g key={i}>
              <line x1={cx} y1={cy} x2={p.x} y2={p.y} stroke={b.c.step3} strokeOpacity={0.55} strokeWidth={4}
                strokeDasharray={len} strokeDashoffset={len * (1 - draw)} strokeLinecap="round" />
              {live && <rect x={px - 8} y={py - 8} width={16} height={16} rx={4} fill={b.c.step2} opacity={Math.sin(t * Math.PI)} />}
            </g>
          );
        })}
      </svg>
      <div style={{ position: "absolute", left: cx - 100, top: cy - 100, width: 200, height: 200, transform: `scale(${(0.6 + center * 0.4) * (1 + 0.05 * kick)})`, opacity: center }}>
        <Img src={b.icon} style={{ width: 200, height: 200, borderRadius: 46, boxShadow: `0 0 0 ${12 + Math.sin(f / 8) * 5}px ${b.c.brandSubtle}, 0 20px 50px rgba(63,51,176,.25)` }} />
      </div>
      {s.nodes.map((nd, i) => {
        const p = interpolate(f, [(0.75 + i * 0.25) * FPS, (1.05 + i * 0.25) * FPS], [0, 1], { ...clamp, easing: Easing.bezier(0.34, 1.4, 0.64, 1) });
        return (
          <div key={i} style={{
            position: "absolute", left: pts[i].x - 190, top: pts[i].y - 50, width: 380, height: 100,
            background: b.c.surface, border: `1.5px solid ${b.c.border}`, borderRadius: 18,
            boxShadow: "0 10px 30px rgba(30,27,75,.08)",
            display: "flex", alignItems: "center", gap: 18, padding: "0 22px",
            opacity: p, transform: `scale(${0.85 + p * 0.15})`,
          }}>
            <IconTile name={nd.icon} b={b} size={58} />
            <div>
              <div style={{ fontSize: 30, fontWeight: 800, color: b.c.text, letterSpacing: "-0.02em", lineHeight: 1.1 }}>{nd.label}</div>
              <div style={{ fontSize: 20, color: b.c.subtle, marginTop: 3 }}>{nd.text}</div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/** Stepper of rounded squares. Done = step 3 with a check, current = action color, next = neutral. */
const Steps: React.FC<{ steps: { text: string; icon: string }[]; b: B; start: number; every: number }> = ({ steps, b, start, every }) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const cur = Math.floor((t - start) / every);
  return (
    <div style={{ display: "flex", flexDirection: "column" }}>
      {steps.map((st, i) => {
        const p = interpolate(t, [start + i * every, start + i * every + 0.4], [0, 1], { ...clamp, easing: ease });
        const done = i < cur, now = i === cur;
        const line = interpolate(t, [start + (i + 1) * every - 0.3, start + (i + 1) * every], [0, 1], clamp);
        return (
          <div key={i} style={{ display: "flex", gap: 24, minHeight: 116 }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 60 }}>
              <div style={{
                width: 60, height: 60, borderRadius: 16, display: "grid", placeItems: "center", opacity: 0.4 + p * 0.6,
                background: done ? b.c.step3 : now ? b.c.brand : b.c.surface, border: done || now ? "none" : `1.5px solid ${b.c.border}`,
                transform: `scale(${now ? 1.08 : 1})`, boxShadow: now ? "0 10px 24px rgba(63,51,176,.3)" : "none",
              }}>
                {done ? <Icon name="Check" size={30} color="#fff" stroke={3} /> : <Icon name={st.icon} size={28} color={now ? b.c.onBrand : b.c.subtle} />}
              </div>
              {i < steps.length - 1 && (
                <div style={{ flex: 1, width: 5, background: b.c.border, borderRadius: 3, margin: "6px 0", overflow: "hidden" }}>
                  <div style={{ height: `${line * 100}%`, background: b.c.step3 }} />
                </div>
              )}
            </div>
            <div style={{ ...rise(p, 16), fontSize: 34, fontWeight: now ? 700 : 600, color: now || done ? b.c.text : b.c.subtle, paddingTop: 10, lineHeight: 1.2, textWrap: "balance" }}>
              <Rich text={st.text} accent={b.c.accent} />
            </div>
          </div>
        );
      })}
    </div>
  );
};

const UseCase: React.FC<{ s: Extract<Scene, { kind: "usecase" }>; b: B }> = ({ s, b }) => {
  const pm = useIn(0.25, 0.5);
  const bpm = React.useContext(BpmCtx);
  const beat = 60 / bpm;
  const every = Math.max(2, Math.floor((s.sec - 1.5) / beat / s.steps.length)) * beat;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 110, top: 96, width: 780 }}>
        <Title text={s.title} b={b} size={54} eyebrow={s.eyebrow} icon={s.icon} align="left" />
        <div style={{ marginTop: 46 }}><Steps steps={s.steps} b={b} start={2 * beat} every={every} /></div>
      </div>
      <div style={{ position: "absolute", left: 950, top: 130, width: 890, height: 820, opacity: pm, transform: `translateX(${(1 - pm) * 60}px)` }}>
        <MediaBox m={s.media} b={b} sec={s.sec} />
      </div>
    </AbsoluteFill>
  );
};

const Portal: React.FC<{ s: Extract<Scene, { kind: "portal" }>; b: B }> = ({ s, b }) => {
  const f = useCurrentFrame();
  const w = 540, gap = 50, left = (1920 - (w * s.panes.length + gap * (s.panes.length - 1))) / 2;
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 64, left: 160, right: 160 }}><Title text={s.title} b={b} size={60} /></div>
      {s.panes.map((pn, i) => {
        const p = interpolate(f, [(0.5 + i * 0.5) * FPS, (0.85 + i * 0.5) * FPS], [0, 1], { ...clamp, easing: Easing.bezier(0.34, 1.3, 0.64, 1) });
        return (
          <div key={i} style={{ position: "absolute", left: left + i * (w + gap), top: 210, width: w, ...rise(p, 50) }}>
            <div style={{ position: "relative", height: 640 }}><MediaBox m={pn.media} b={b} sec={s.sec} bar={46} /></div>
            <div style={{ marginTop: 26, display: "flex", alignItems: "center", justifyContent: "center", gap: 14, fontSize: 31, fontWeight: 700, color: b.c.text }}>
              <IconTile name={pn.icon} b={b} size={48} /><span><Rich text={pn.caption} accent={b.c.accent} /></span>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const Chat: React.FC<{ s: Extract<Scene, { kind: "chat" }>; b: B }> = ({ s, b }) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const typeEnd = 0.8 + Math.min(2.6, s.prompt.length * 0.022);
  const shown = Math.floor(interpolate(t, [0.8, typeEnd], [0, s.prompt.length], clamp));
  const callStart = Math.ceil((typeEnd + 0.3) * 2) / 2, callEvery = 0.5;
  const replyAt = callStart + s.calls.length * callEvery + 0.5;
  const mediaAt = replyAt + 1.0;
  const pr = useIn(replyAt, 0.5);
  const pm = useIn(mediaAt, 0.6);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 56, left: 160, right: 160 }}><Title text={s.title} b={b} size={56} /></div>
      <div style={{ position: "absolute", left: 90, top: 190, width: 900, height: 840, background: b.c.surface, border: `1.5px solid ${b.c.border}`, borderRadius: 22, padding: 30, display: "flex", flexDirection: "column", gap: 18, fontSize: 25, overflow: "hidden", boxShadow: "0 24px 60px rgba(30,27,75,.12)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, color: b.c.subtle, fontSize: 22, fontWeight: 600 }}>
          <IconTile name="Bot" b={b} size={40} />{s.label}
        </div>
        <div style={{ alignSelf: "flex-end", maxWidth: 700, background: b.c.brand, color: b.c.onBrand, padding: "16px 22px", borderRadius: "18px 18px 4px 18px", fontWeight: 600, lineHeight: 1.35, minHeight: 50 }}>
          {s.prompt.slice(0, shown)}{shown < s.prompt.length && <span style={{ opacity: Math.round(t * 3) % 2 }}>▍</span>}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {s.calls.map((c, i) => {
            const at = callStart + i * callEvery;
            const p = interpolate(t, [at, at + 0.3], [0, 1], { ...clamp, easing: ease });
            const ok = t > at + 0.4;
            return (
              <div key={i} style={{ ...rise(p, 10), display: "flex", alignItems: "center", gap: 14, fontSize: 21, color: b.c.subtle }}>
                <div style={{ width: 28, height: 28, borderRadius: 8, display: "grid", placeItems: "center", background: ok ? b.c.step3 : b.c.border }}>
                  {ok && <Icon name="Check" size={18} color="#fff" stroke={3} />}
                </div>
                <code style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", color: b.c.step1, background: b.c.brandSubtle, padding: "3px 10px", borderRadius: 6 }}>{c.tool}</code>
                <span>{c.text}</span>
              </div>
            );
          })}
        </div>
        <div style={{ ...rise(pr, 14), background: b.c.bg, border: `1.5px solid ${b.c.border}`, color: b.c.text, padding: "18px 22px", borderRadius: "18px 18px 18px 4px", lineHeight: 1.4, whiteSpace: "pre-line" }}>
          <Rich text={s.reply} accent={b.c.accent} />
        </div>
        {s.note && <div style={{ marginTop: "auto", fontSize: 18, color: b.c.subtle }}>{s.note}</div>}
      </div>
      <div style={{ position: "absolute", left: 1030, top: 280, width: 830, height: 600, opacity: pm, transform: `translateX(${(1 - pm) * 60}px)` }}>
        <MediaBox m={s.media} b={b} sec={s.sec - mediaAt} />
      </div>
      <div style={{ position: "absolute", left: 1030, top: 910, width: 830, textAlign: "center", fontSize: 28, fontWeight: 700, color: b.c.text, ...rise(pm, 10) }}>
        <Rich text={s.caption} accent={b.c.accent} />
      </div>
    </AbsoluteFill>
  );
};

const Grid: React.FC<{ s: Extract<Scene, { kind: "grid" }>; b: B }> = ({ s, b }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", top: 56, left: 160, right: 160 }}><Title text={s.title} b={b} size={60} /></div>
      <div style={{ position: "absolute", top: 190, left: 100, right: 100, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 20 }}>
        {s.items.map((it, i) => {
          const at = 0.5 + i * 0.25;
          const p = interpolate(f, [at * FPS, (at + 0.3) * FPS], [0, 1], { ...clamp, easing: Easing.bezier(0.34, 1.5, 0.64, 1) });
          return (
            <div key={i} style={{ opacity: Math.min(1, p * 1.4), transform: `translateY(${(1 - p) * 30}px) scale(${0.92 + 0.08 * p})`, background: b.c.surface, border: `1.5px solid ${b.c.border}`, borderRadius: 18, padding: "20px 22px", height: 180, display: "flex", gap: 18, boxShadow: "0 8px 24px rgba(30,27,75,.06)" }}>
              <IconTile name={it.icon} b={b} size={60} />
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ fontSize: 28, fontWeight: 800, color: b.c.text, letterSpacing: "-0.02em", lineHeight: 1.1 }}>{it.title}</div>
                <div style={{ fontSize: 21, color: b.c.subtle, lineHeight: 1.3 }}>{it.text}</div>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** Big words, one every `everyBeats`, alternating the brand steps; a row of step squares counts along. */
const Kinetic: React.FC<{ s: Extract<Scene, { kind: "kinetic" }>; b: B }> = ({ s, b }) => {
  const f = useCurrentFrame();
  const bpm = React.useContext(BpmCtx);
  const step = (60 / bpm) * s.everyBeats * FPS;
  const idx = Math.min(s.words.length - 1, Math.floor(f / step));
  const local = f - idx * step;
  const p = interpolate(local, [0, 6], [0, 1], { ...clamp, easing: Easing.bezier(0.34, 1.6, 0.64, 1) });
  const colors = [b.c.step1, b.c.step2, b.c.brand, b.c.step2];
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ display: "flex", gap: 22, marginBottom: 50 }}>
        {s.words.map((_, i) => (
          <div key={i} style={{ width: 22 + (i <= idx ? 8 : 0), height: 22 + (i <= idx ? 8 : 0), borderRadius: 7, background: i < idx ? b.c.step3 : i === idx ? b.c.brand : b.c.border, alignSelf: "center" }} />
        ))}
      </div>
      <div style={{ fontSize: 210, fontWeight: 900, letterSpacing: "-0.05em", color: colors[idx % colors.length], transform: `scale(${0.7 + 0.3 * p}) translateY(${(1 - p) * 30}px)`, opacity: p }}>
        {s.words[idx]}
      </div>
    </AbsoluteFill>
  );
};

const End: React.FC<{ s: TourSpec; b: B }> = ({ s, b }) => {
  const pc = useIn(0.9, 0.5);
  const pt = useIn(1.2, 0.5);
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", gap: 34 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 24 }}>
        <BuildMark b={b} size={130} at={0.1} />
        <div style={{ fontSize: 92, fontWeight: 800, letterSpacing: "-0.04em", lineHeight: 1, color: b.c.text, opacity: useIn(0.5, 0.5) }}>{b.t.name}</div>
      </div>
      {s.cta && <div style={{ ...rise(pc), fontSize: 60, fontWeight: 800, color: b.c.text, letterSpacing: "-0.02em" }}>{s.cta}</div>}
      {s.showTagline && <div style={{ ...rise(pt), fontSize: 32, color: b.c.subtle, fontWeight: 500 }}>{b.t.tagline}</div>}
    </AbsoluteFill>
  );
};

/** Scenes push: the old one slides left as the wipe covers it, the new one slides in behind the wipe. */
const Shell: React.FC<{ dur: number; children: React.ReactNode }> = ({ dur, children }) => {
  const f = useCurrentFrame();
  const pout = interpolate(f, [dur - 8, dur], [0, 1], { ...clamp, easing: Easing.in(Easing.cubic) });
  const pin = interpolate(f, [0, 10], [0, 1], { ...clamp, easing: ease });
  return (
    <AbsoluteFill style={{ transform: `translateX(${(1 - pin) * 120 - pout * 160}px) scale(${1 - pout * 0.04})` }}>
      {children}
    </AbsoluteFill>
  );
};

/** Branded wipe on a cut: three skewed panels in the step colours sweep across, centred on the cut frame. */
const Wipe: React.FC<{ at: number; b: B }> = ({ at, b }) => {
  const f = useCurrentFrame();
  const half = 8;
  const cols = [b.c.step1, b.c.step2, b.c.step3];
  if (f < at - half - 6 || f > at + half + 6) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {cols.map((c, i) => {
        const d = i * 2;
        const inP = interpolate(f, [at - half - 4 + d, at - 2 + d], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
        const outP = interpolate(f, [at + d - 2, at + half + d], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
        const x = (1 - inP) * 120 - outP * 125;
        return <div key={i} style={{ position: "absolute", top: "-10%", bottom: "-10%", left: `${x - 10}%`, width: "120%", background: c, borderRadius: 80, transform: "skewX(-12deg)", zIndex: 3 - i }} />;
      })}
    </AbsoluteFill>
  );
};

/** Progress along the bottom: small rounded squares, done step 3, current action. */
const Progress: React.FC<{ s: TourSpec; b: B }> = ({ s, b }) => {
  const f = useCurrentFrame();
  let acc = 0;
  const starts = s.scenes.map((sc) => { const st = acc; acc += Math.round(sc.sec * FPS); return st; });
  const idx = starts.filter((st) => f >= st).length - 1;
  if (f >= acc) return null;
  return (
    <div style={{ position: "absolute", bottom: 32, left: 0, right: 0, display: "flex", justifyContent: "center", alignItems: "center" }}>
      {s.scenes.map((_, i) => (
        <React.Fragment key={i}>
          {i > 0 && <div style={{ width: 30, height: 3, background: i <= idx ? b.c.step3 : b.c.border }} />}
          <div style={{ width: 14, height: 14, borderRadius: 4, background: i < idx ? b.c.step3 : i === idx ? b.c.brand : b.c.border }} />
        </React.Fragment>
      ))}
    </div>
  );
};

const Music: React.FC<{ s: TourSpec }> = ({ s }) => {
  const { durationInFrames } = useVideoConfig();
  if (!s.music) return null;
  const duck = (f: number) => s.voice.reduce((g, v) => {
    const a = v.at * FPS, e = (v.at + v.sec) * FPS;
    return Math.min(g, interpolate(f, [a - 6, a, e, e + 8], [1, v.duckTo, v.duckTo, 1], clamp));
  }, 1);
  return <Audio src={staticFile(s.music)} volume={(f) => interpolate(f, [0, 10, durationInFrames - 45, durationInFrames], [0, s.musicVolume, s.musicVolume, 0], clamp) * duck(f)} />;
};

export const Tour: React.FC<TourSpec> = (props) => {
  const s = tourSpec.parse(props);
  const b = useBrand(s.brand, s.theme);
  let from = 0;
  const cuts: number[] = [];
  s.scenes.reduce((acc, sc) => { const e = acc + Math.round(sc.sec * FPS); cuts.push(e); return e; }, 0);
  return (
    <BpmCtx.Provider value={s.bpm}>
    <AbsoluteFill style={{ background: b.c.bg, fontFamily: b.font }}>
      {s.scenes.map((sc, i) => {
        const dur = Math.round(sc.sec * FPS);
        const start = from;
        from += dur;
        const body =
          sc.kind === "opener" ? <Opener s={sc} b={b} /> :
          sc.kind === "hub" ? <Hub s={sc} b={b} /> :
          sc.kind === "usecase" ? <UseCase s={sc} b={b} /> :
          sc.kind === "portal" ? <Portal s={sc} b={b} /> :
          sc.kind === "chat" ? <Chat s={sc} b={b} /> :
          sc.kind === "kinetic" ? <Kinetic s={sc} b={b} /> :
          <Grid s={sc} b={b} />;
        return <Sequence key={i} from={start} durationInFrames={dur}><Shell dur={dur}>{body}</Shell></Sequence>;
      })}
      <Sequence from={from}><End s={s} b={b} /></Sequence>
      <Progress s={s} b={b} />
      {cuts.map((c, i) => <Wipe key={i} at={c} b={b} />)}
      {s.voice.map((v, i) => (
        <Sequence key={`v${i}`} from={Math.round(v.at * FPS)}><Audio src={staticFile(v.src)} volume={v.volume} /></Sequence>
      ))}
      <Music s={s} />
    </AbsoluteFill>
    </BpmCtx.Provider>
  );
};
