// Copies each brand's assets, stills and footage into public/ and collects its tokens for src/brand.ts.
// Runs before studio, render and typecheck. Copies instead of symlinks so it also works on Windows.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const video = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const brandsDir = path.join(video, "..", "brands");
const pub = path.join(video, "public");

const tokens = {};
for (const d of fs.readdirSync(brandsDir, { withFileTypes: true })) {
  const file = path.join(brandsDir, d.name, "tokens.json");
  if (!d.isDirectory() || d.name.startsWith("_") || !fs.existsSync(file)) continue;
  tokens[d.name] = JSON.parse(fs.readFileSync(file, "utf8"));
  for (const [from, to] of [["assets", `brands/${d.name}/assets`], ["stills", `brands/${d.name}/stills`], ["footage", `footage/${d.name}`]]) {
    const src = path.join(brandsDir, d.name, from);
    const dst = path.join(pub, to);
    fs.rmSync(dst, { recursive: true, force: true });
    if (fs.existsSync(src)) fs.cpSync(src, dst, { recursive: true, dereference: true });
  }
}
fs.writeFileSync(path.join(video, "src", "brands.generated.json"), JSON.stringify(tokens, null, 2));
console.log(`brands: ${Object.keys(tokens).join(", ") || "none"}`);
