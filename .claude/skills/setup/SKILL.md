---
name: setup
description: First-time setup of this workspace for a new user. Creates profile.md, an optional theme and company template mapping, and checks the installed tools. Use when profile.md is missing or the user asks to set up or reconfigure the workspace.
---

1. **Profile.** If `profile.md` exists, show it and ask what to change. Otherwise ask, in one batch, for the
   fields in `profile.example.md` and write `profile.md`. Leave unanswered fields out.
2. **Theme.** Ask whether they have a company deck/document template.
   - **No:** ask for organization name, two colors and a logo file (optional, all can be skipped). Copy
     `templates/theme.json` to `templates/theme.local.json`, set `identity`, `colors`, `fonts`, point both
     `template` paths into `templates/private/`, then run
     `uv run tools/docs/make_templates.py --theme templates/theme.local.json`.
   - **Yes:** ask them to put the files in `templates/private/` (not in git). Follow "Use your own template"
     in `tools/docs/README.md` to write `templates/theme.local.json`.
   Then build both files in `tools/docs/examples/` with their theme and ask them to open the result.
3. **Tools.** Check which are installed and say what each missing one blocks:
   `uv` (decks and documents), `node` + `pnpm` (video and images), `ffmpeg` (video), `soffice` (visual check
   of documents, optional). Do not install anything without asking.
4. **Jira (optional).** If they use Jira, copy `.env.example` to `.env` for them to fill in. Never ask for
   tokens in chat.
5. **Marketing (optional).** Offer `/new-brand`.

End with what is ready and what is still open.
