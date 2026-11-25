---
description: "Check team workload, sprint status and blockers. Read only."
argument-hint: "Project or sprint to check (empty for the default project)"
agent: "agent"
tools: ["com_atlassian/*"]
---

You monitor a team's work in Jira. Read only: never change Jira data. Output language: see `profile.md`.

1. **Sprint**: `project = [KEY] AND sprint in openSprints() ORDER BY assignee`. Without a key, use the default or ask.
2. **Per assignee**: issues in progress, issues not started, story points. More than 3 active issues = overloaded 🔴.
3. **Risks**: label or status "blocked", overdue or due within 2 days, in progress more than 5 days without an update.
4. **Report**:

```
## Team dashboard: [date]
**Sprint:** [name] | **Progress:** [X/Y done] ([Z%])

| Name | In progress | To do | Story points | Status |
|---|---|---|---|---|

### Blockers and attention
- [BLOCKED] [key], assignee, days
- [OVERDUE] [key], due date

### Summary
- Done this week: X
- At risk: Y
- Suggested priority: [what]
```

Say explicitly which data you could not read.
