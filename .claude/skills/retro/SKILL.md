---
name: retro
description: Record the user's feedback on marketing content and turn it into lasting rules, so the marketer improves over time. Use whenever the user reacts to a rendered asset or copy ("too fast", "I like this hook", "don't say X", performance numbers from TikTok).
---

Arguments: `<brand> [campaign]`. If the feedback is unclear, ask one question.

1. **Classify** each point:
   - *Brand-specific* (voice, words, colors, a claim) → `brands/<brand>/`
   - *Channel or craft* that applies to every brand (caption pace, hook length, safe area) → `playbook/`
   - *A bug in the tooling* (layout, render) → fix the code in `video/` or `tools/`
   - *Performance data* (views, watch time, CTR) → `playbook/results.md` table with date, brand, asset, numbers
2. **Write the learning** at the top of `brands/<brand>/learnings.md` (or `playbook/what-works.md`):
   date, campaign, what was said (quote it), the rule it becomes, where the rule lives.
3. **Make it enforceable** where possible:
   - a banned word or spelling → `lexicon.json` (checked by `slop_check.py`)
   - a generic slop pattern → `tools/slop_check.py` BANNED list and `ANTI-SLOP.md`
   - a layout/timing default → `video/src/` (e.g. caption size, minimum caption duration)
4. **Promote** a learning into `brand.md` (or `ANTI-SLOP.md`) once it has held in two campaigns, and mark
   it "promoted" in the log. Remove rules the user later contradicts; note why.
5. **Apply** it: if the asset is still in progress, re-render with the fix.
6. Append one line to `playbook/CHANGELOG.md`: date, what changed, why.

Show the user the diff of every rule you changed. Never loosen a brand rule without their explicit say-so.
