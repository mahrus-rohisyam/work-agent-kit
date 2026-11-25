---
name: new-brand
description: Add a new product/brand to the marketing workspace with its own voice, tokens and rules. Use when the user wants marketing for a product that has no folder in brands/.
---

Arguments: `<brand-slug> [product repo path]`.

1. `cp -r brands/_template brands/<slug>`.
2. Read the product's own brand/design docs, README, features docs and theme tokens (if a repo exists).
   Fill `brand.md` (front matter paths, positioning, audience, provable messages, voice with
   instead/write table, channels, checklist), `tokens.json`, `lexicon.json`. Copy logo files to `assets/`
   (names as in `tokens.json` → `logo`; the mark is square).
   Leave a field as `TODO(ask)` instead of guessing; then ask the user those questions in one batch.
3. Tokens are picked up by `video/scripts/sync-brands.mjs` before each render. If the brand uses a
   font other than Inter, add its woff2 to `video/public/fonts/` and a `loadFont` call.
4. Put demo videos in `brands/<slug>/footage/` (not in git; a symlink to the product's media folder also
   works). Specs refer to them as `footage/<slug>/<file>`, and to stills as `brands/<slug>/stills/<file>`.
5. Render one `og.json` test card and show it.
6. Never copy another brand's voice, messages or lexicon; start from the template.
