---
name: refresh
description: Research what changed in marketing channels, content tactics and our free tooling, and update the playbook with dated, sourced notes. Use monthly, when a playbook page is older than 60 days, or when the user asks "what's new in TikTok/marketing/tools".
---

Arguments: optional focus (`channels`, `tactics`, `tools`, or a platform name). Default: all.

1. Read `playbook/*.md` and note each page's "last verified" date.
2. **Channels**: search for current specs and rules for TikTok, Instagram Reels, YouTube Shorts,
   LinkedIn, X and landing-page video (safe areas, lengths, aspect ratios, caption and music rules,
   AI-content labeling policy). Prefer official help/creator pages over blogs.
3. **Tactics**: search for recent, evidence-backed findings on short-form B2B/SaaS content (hooks,
   length, captions, posting cadence). Discard listicles with no data. Mark each note
   `evidence: official | data | opinion`.
4. **Tools**: run `cd video && pnpm outdated`; read Remotion release notes for breaking changes and
   license changes; search for new free/open-source tools that run on CPU (captions, TTS voices,
   music, background removal). Note each with license and CPU fit. Do not install anything.
5. **Write**: update the affected `playbook/` pages in place, each fact with a source URL and the date
   checked; set "last verified". Add a "Proposed changes" section to `playbook/CHANGELOG.md` for
   anything that would change rules, code or brand files. Apply those only after the user agrees.
6. Report: 5–10 bullet summary of what changed and what you propose.
