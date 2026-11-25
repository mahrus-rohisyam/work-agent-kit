import { staticFile } from "remotion";
import { loadFont } from "@remotion/fonts";
import generated from "./brands.generated.json"; // written by scripts/sync-brands.mjs from brands/*/tokens.json

// Fonts are loaded from video/public/fonts; loadFont delays rendering until ready.
loadFont({ family: "Inter", url: staticFile("fonts/inter-latin-wght-normal.woff2"), weight: "100 900" });

type Palette = {
  bg: string; surface: string; text: string; subtle: string; brand: string; onBrand: string; accent: string;
  brandSubtle: string; border: string; step1: string; step2: string; step3: string;
};
type Tokens = {
  name: string;
  tagline: string;
  font: { family: string; fallback: string };
  logo: { light: string; dark: string; mark: string; markDark?: string; icon: string };
  light: Palette;
  dark: Palette;
  gradient: string[] | null;
  radius: { sm: number; md: number; lg: number };
};
const BRANDS: Record<string, Tokens> = generated;

export const useBrand = (brand: string, theme: "dark" | "light") => {
  const t = BRANDS[brand];
  if (!t) throw new Error(`Unknown brand "${brand}". Add brands/${brand}/tokens.json.`);
  const c = t[theme];
  return {
    t,
    c,
    font: `${t.font.family}, ${t.font.fallback}`,
    // Brands without a gradient get their solid brand color.
    gradient: t.gradient ? `linear-gradient(135deg, ${t.gradient[0]}, ${t.gradient[1]})` : c.brand,
    logo: staticFile(`brands/${brand}/assets/${theme === "dark" ? t.logo.dark : t.logo.light}`),
    mark: staticFile(`brands/${brand}/assets/${theme === "dark" && t.logo.markDark ? t.logo.markDark : t.logo.mark}`),
    icon: staticFile(`brands/${brand}/assets/${t.logo.icon}`),
  };
};
