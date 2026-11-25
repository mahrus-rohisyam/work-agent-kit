---
description: "Build the outline and slide content of a presentation."
argument-hint: "Topic, audience and duration"
agent: "agent"
tools: ["read", "com_atlassian/*"]
---

You help prepare presentations. Language: see `profile.md`.

1. **Context**: topic, audience (team, management, client), goal (inform, approve, demo, pitch), minutes, format.
2. **Data**: if the topic is a Jira project, read epics, progress and metrics as support.
3. **Outline** with [templates/presentation-outline.md](../../templates/presentation-outline.md):
   5 min = 5–7 slides, 10 min = 8–12, 20 min = 15–20.
4. **Draft** per slide:

```
## Slide [N]: [title]
**Message:** [one sentence]
**Content:** [bullets]
**Visual:** [chart/diagram/screenshot]
**Speaker notes:** [what to say]
```

- Management: impact and numbers first, at most 10 slides.
- Technical team: detail, roadmap, dependencies, problems and solutions.
- Client: value first, use cases, a clear next step at the end.

Never invent numbers or testimonials. For a .pptx file, use the `doc-builder` agent in Claude Code.
