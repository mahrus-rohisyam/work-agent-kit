---
name: campaign
description: Make a marketing campaign or single asset (TikTok/Reels video, landing-page loop, square video, social post, OG card) for a brand in this workspace. Use for "make a video/post/ad about <feature> for <brand>".
---

Delegate to the `marketer` agent, or follow `.claude/agents/marketer.md` yourself when already
acting as it. Arguments: `<brand> <what>` (e.g. `acme tiktok about search filters`).

Minimum deliverable per campaign unless the user says otherwise:
- `vertical.json` → TikTok/Reels/Shorts (15–35 s, music + captions)
- `landscape.json` → landing page loop (no captions, ≤ 20 s) and its poster .jpg
- `og.json` → link card

End with: output paths, the copy used, and one question asking for feedback.
