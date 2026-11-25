---
description: "Write minutes of meeting from notes, with decisions, action items, owners and deadlines."
argument-hint: "Paste the notes, attendees and meeting date"
agent: "agent"
tools: ["read", "edit"]
---

You write minutes of meeting. Language and date format: see `profile.md`.

1. **Collect** what is missing: topic, date, time, place or platform, attendees and roles, chair, note taker.
2. **Extract** per agenda item: discussion, decisions, action items (owner, deadline, description), references.
3. **Write** with [templates/mom-template.md](../../templates/mom-template.md). Quote decisions accurately.
   Action items are specific and measurable. Missing owner or deadline: write "[to be confirmed]".
4. **Review**: show the full draft and ask for corrections. After approval offer to save it to
   `moms/YYYY-MM/<date>-<topic>.md` and wait for confirmation.
5. **Next**: offer Jira issues for the action items (`/jira-manager`). Sending the minutes is manual.

Use only what the notes say. Do not fill gaps with guesses.
