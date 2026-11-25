import { z } from "zod";

// One spec drives every composition. The marketer writes it as JSON in
// brands/<brand>/briefs/<campaign>/<asset>.json and renders it with --props.

export const focusKey = z.object({
  at: z.number().describe("seconds from the start of the clip"),
  x: z.number().min(0).max(1).default(0.5),
  y: z.number().min(0).max(1).default(0.5),
  zoom: z.number().min(1).max(3).default(1),
});

export const caption = z.object({
  from: z.number().describe("seconds from the start of the video"),
  to: z.number(),
  text: z.string(),
});

export const spec = z.object({
  brand: z.string().default("example"),
  theme: z.enum(["dark", "light"]).default("dark"),
  hook: z.string().default(""),
  clip: z.object({
    src: z.string().describe("path under video/public, e.g. footage/<brand>/demo.mp4"),
    startSec: z.number().default(0),
    endSec: z.number(),
    playbackRate: z.number().default(1),
    focus: z.array(focusKey).default([]),
  }),
  captions: z.array(caption).default([]),
  cta: z.string().default(""),
  showTagline: z.boolean().default(true),
  endCardSec: z.number().default(2.5),
  music: z.string().optional().describe("path under video/public, e.g. music/pad-a.m4a"),
  musicVolume: z.number().default(0.35),
});

export type Spec = z.infer<typeof spec>;

export const stillSpec = z.object({
  brand: z.string().default("example"),
  theme: z.enum(["dark", "light"]).default("dark"),
  eyebrow: z.string().default(""),
  headline: z.string(),
  body: z.string().default(""),
  image: z.string().optional().describe("still under video/public, e.g. brands/<brand>/stills/board.png"),
  imageFocus: focusKey.omit({ at: true }).default({ x: 0.5, y: 0.5, zoom: 1 }),
  cta: z.string().default(""),
});

export type StillSpec = z.infer<typeof stillSpec>;

export const FPS = 30;
export const clipSeconds = (s: Spec) => (s.clip.endSec - s.clip.startSec) / s.clip.playbackRate;
export const totalFrames = (s: Spec) => Math.round((clipSeconds(s) + s.endCardSec) * FPS);
