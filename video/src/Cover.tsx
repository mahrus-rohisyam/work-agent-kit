import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { z } from "zod";
import { useBrand } from "./brand";

// Title slide / deck cover, 16:9. Left: logo, title, subtitle, footer. Right: the brand mark as a large
// supergraphic bleeding off the edge, optionally with a product screenshot in an app frame.

export const coverSpec = z.object({
  brand: z.string().default("example"),
  theme: z.enum(["dark", "light"]).default("light"),
  eyebrow: z.string().default(""),
  title: z.string(),
  sub: z.string().default(""),
  footer: z.string().default(""),
  image: z.string().optional(),
  imageLabel: z.string().default(""),
  imageX: z.number().default(0),
  imageY: z.number().default(0),
  imageCropTop: z.number().default(0).describe("px of the screenshot's top hidden (e.g. the app bar with an old logo)"),
});
export type CoverSpec = z.infer<typeof coverSpec>;

/** *word* in the accent colour. */
const Rich: React.FC<{ text: string; accent: string }> = ({ text, accent }) => (
  <>{text.split(/(\*[^*]+\*)/g).filter(Boolean).map((s, i) =>
    s.startsWith("*") ? <span key={i} style={{ color: accent }}>{s.slice(1, -1)}</span> : <span key={i}>{s}</span>)}</>
);

export const Cover: React.FC<CoverSpec> = (props) => {
  const s = coverSpec.parse(props);
  const b = useBrand(s.brand, s.theme);
  const S = s.image ? 760 : 1180;
  const pos = s.image ? { left: 1180, top: -150 } : { left: 1010, top: -120 };
  return (
    <AbsoluteFill style={{ background: b.c.bg, fontFamily: b.font, overflow: "hidden" }}>
      <Img src={b.mark} style={{ position: "absolute", width: S, height: S, ...pos }} />

      {s.image && (
        <div style={{ position: "absolute", left: 1000, top: 330, width: 1060, height: 640, borderRadius: 22, overflow: "hidden", background: b.c.surface, border: `1.5px solid ${b.c.border}`, boxShadow: "0 30px 80px rgba(30,27,75,.20), 0 6px 16px rgba(30,27,75,.08)" }}>
          <div style={{ height: 58, display: "flex", alignItems: "center", gap: 14, padding: "0 24px", borderBottom: `1.5px solid ${b.c.border}` }}>
            <Img src={b.mark} style={{ height: 32 }} />
            <span style={{ fontSize: 24, fontWeight: 700, color: b.c.text }}>{b.t.name}</span>
            {s.imageLabel && <span style={{ fontSize: 22, color: b.c.subtle }}>· {s.imageLabel}</span>}
          </div>
          <div style={{ height: "calc(100% - 58px)", overflow: "hidden" }}>
            <Img src={staticFile(s.image)} style={{ width: "100%", height: `calc(100% + ${s.imageCropTop}px)`, marginTop: -s.imageCropTop, objectFit: "cover", objectPosition: `${s.imageX * 100}% ${s.imageY * 100}%` }} />
          </div>
        </div>
      )}

      <div style={{ position: "absolute", left: 140, top: 120, bottom: 110, width: s.image ? 780 : 860, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
        <Img src={b.logo} style={{ height: 72, alignSelf: "flex-start" }} />
        <div style={{ display: "flex", flexDirection: "column", gap: 30 }}>
          {s.eyebrow && <div style={{ fontSize: 28, fontWeight: 700, color: b.c.accent, letterSpacing: "0.08em", textTransform: "uppercase" }}>{s.eyebrow}</div>}
          <div style={{ fontSize: 104, fontWeight: 800, lineHeight: 1.02, letterSpacing: "-0.035em", color: b.c.text, textWrap: "balance" }}>
            <Rich text={s.title} accent={b.c.accent} />
          </div>
          {s.sub && <div style={{ fontSize: 38, lineHeight: 1.35, color: b.c.subtle, textWrap: "pretty" }}>{s.sub}</div>}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16, fontSize: 26, color: b.c.subtle, fontWeight: 500 }}>
          <div style={{ display: "flex", gap: 8 }}>
            {[b.c.step1, b.c.step2, b.c.step3].map((c, i) => <div key={i} style={{ width: 14, height: 14, borderRadius: 4, background: c }} />)}
          </div>
          {s.footer}
        </div>
      </div>
    </AbsoluteFill>
  );
};
