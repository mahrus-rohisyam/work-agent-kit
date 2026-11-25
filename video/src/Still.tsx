import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { StillSpec } from "./spec";
import { useBrand } from "./brand";

/** Social post (4:5) and link/OG card (1.91:1) from one spec. */
export const SocialStill: React.FC<StillSpec & { layout: "post" | "og" }> = (s) => {
  const b = useBrand(s.brand, s.theme);
  const og = s.layout === "og";
  const f = s.imageFocus;
  const text = (
    <div style={{ display: "flex", flexDirection: "column", gap: og ? 18 : 28 }}>
      {s.eyebrow && <div style={{ fontSize: og ? 24 : 32, fontWeight: 600, color: b.c.accent, letterSpacing: "0.04em", textTransform: "uppercase" }}>{s.eyebrow}</div>}
      <div style={{ fontSize: og ? 60 : 84, fontWeight: 800, lineHeight: 1.05, letterSpacing: "-0.03em", color: b.c.text, textWrap: "balance" }}>{s.headline}</div>
      {s.body && <div style={{ fontSize: og ? 26 : 36, lineHeight: 1.35, color: b.c.subtle, textWrap: "pretty" }}>{s.body}</div>}
      {s.cta && <div style={{ fontSize: og ? 26 : 34, fontWeight: 600, color: b.c.brand }}>{s.cta}</div>}
    </div>
  );
  const shot = s.image && (
    <div style={{ flex: 1, minHeight: 0, minWidth: 0, borderRadius: b.t.radius.lg * 2, overflow: "hidden", border: `2px solid ${b.c.border}` }}>
      <Img src={staticFile(s.image)} style={{
        width: "100%", height: "100%", objectFit: "cover",
        objectPosition: `${f.x * 100}% ${f.y * 100}%`, transform: `scale(${f.zoom})`,
        transformOrigin: `${f.x * 100}% ${f.y * 100}%`,
      }} />
    </div>
  );
  return (
    <AbsoluteFill style={{ background: b.c.bg, fontFamily: b.font, padding: og ? 64 : 80, display: "flex", flexDirection: og ? "row" : "column", gap: og ? 56 : 56 }}>
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", flex: og ? "0 0 46%" : "0 0 auto", gap: 40 }}>
        <Img src={b.logo} style={{ height: og ? 52 : 64, alignSelf: "flex-start" }} />
        {text}
      </div>
      {shot}
      {/* the brand gradient once per frame, as the progress line along the bottom */}
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 10, background: b.gradient }} />
    </AbsoluteFill>
  );
};
