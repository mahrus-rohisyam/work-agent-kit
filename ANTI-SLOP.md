# Anti-slop rules

"Slop" is content that could be about any product: generic phrasing, stock visuals, and motion with
no meaning. Every brand's own rules (`brands/<brand>/brand.md`) come on top of these.
`tools/slop_check.py --brand <brand>` enforces the parts a script can check. A human reviews the rest.

## Copy

1. **Specific beats impressive.** Name the feature, the number, the click. "Drag an issue to Done and
   the merge request links itself" beats "Streamline your workflow."
2. **Show the product doing the claim.** A claim with no footage or screenshot behind it is cut.
3. **No filler openers or closers.** No "In today's fast-paced world", "Imagine…", "Say goodbye to…",
   "Look no further", "Ready to…?" questions, or "and so much more".
4. **Banned vocabulary.** The `BANNED` list in `tools/slop_check.py` (delve, seamless, leverage,
   unlock, elevate, game-changer, empower, journey, cutting-edge, …). Plain words instead.
5. **No em dashes, no exclamation marks, no emoji** unless the brand's `lexicon.json` allows them.
6. **Watch lists of three.** AI copy loves "fast, simple, and powerful". Keep a list only when every
   item is concrete and true.
7. **One idea per line on screen.** TikTok captions are 2 to 6 words. Landing headlines are under 8 words.
8. **Write like the brand's user talks.** Use their nouns (sprint, backlog, MR), not marketing nouns
   (solution, platform, ecosystem).
9. **Never invent facts.** Every number, customer, integration or quote must exist in the product
   repo, the docs, or a source the user gave. If you can't cite it, don't write it.

## Visuals

1. **Real UI first.** Recordings and screenshots of the actual product. No fake dashboards.
2. **Brand tokens only.** Colors, fonts and radii come from `brands/<brand>/tokens.json`. No
   default purple-to-pink gradients, glassmorphism blobs, floating 3D shapes or stock "team
   high-fiving" imagery.
3. **One focal point per frame.** Zoom or highlight the part of the UI the caption talks about.
4. **Legible on a phone.** Caption text is at least 56 px on a 1080×1920 frame, inside the TikTok
   safe area (see `brands/<brand>/brand.md` → Channels).
5. **No AI-generated people, logos or fake testimonials.**

## Motion

1. **Motion explains.** It shows order, cause and effect, or where to look. It is not decoration.
2. **Calm easing**, no bounces or spins unless the brand says so. Cuts happen on actions (a click,
   a drop), not on a fixed timer.
3. **Hook in the first 1.5 s** for vertical video: show the result first, then how.

## Review gate

Before anything is called final:

- [ ] `slop_check.py` is clean (errors fixed; each warning is either fixed or deliberately kept)
- [ ] Every claim maps to a source (feature doc, changelog, demo video)
- [ ] Rendered frames checked at phone size (look at 3 stills: 0.5 s, middle, last)
- [ ] The brand's own checklist in `brand.md` passes
