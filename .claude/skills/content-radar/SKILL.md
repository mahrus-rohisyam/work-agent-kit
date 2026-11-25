---
name: content-radar
description: Find new marketing content ideas from a brand's product changes (new features, demo videos, changelog entries) since the last check. Use when the user asks "what should we post", after a product release, or weekly.
---

Arguments: `<brand>` (or `all`).

1. Read `brands/<brand>/brand.md` front matter for `product_repo` and sources, and
   `brands/<brand>/radar.json` for `last_commit` and `last_checked` (create it if missing).
2. In the product repo (read-only): `git log --oneline <last_commit>..HEAD -- docs CHANGELOG.md`,
   diff `features.md` and list new or changed demo videos in the media folder. Ignore internal refactors.
3. For each user-visible change, write an idea in `brands/<brand>/ideas.md` (newest first): date,
   feature, the one message, proof (doc section + demo file), suggested channel and hook, status `new`.
   Also add evergreen ideas when the list of `new` ideas is short.
4. If a message in `brand.md` → "Messages we can prove" is now outdated or a new one is provable,
   propose the edit (don't apply it silently).
5. Update `radar.json` with the new HEAD and today's date. Report the top 3 ideas.
