---
name: idea-to-timeline-panel
description: Turn a raw video idea/logline into a practical timeline story panel and reusable professional video prompts. Use when a user asks for storyboard planning, shot timeline design, mode selection (t2v/i2v/keyframes/multiref), creator-facing panel export, or prompt-pack generation from an initial concept.
---

# Idea To Timeline Panel

Use a two-stage flow: **Claude plans first**, scripts parse and render after.

## Workflow

1. Read user idea and target duration.
2. Make Claude output a compact JSON shot plan (or markdown containing a JSON block).
3. Parse that output into `timeline.plan.json`.
4. Render creator artifacts:
   - `timeline.story.json`
   - `timeline.panel.json`
   - `panel.md`
   - `panel.html`
   - `index.html`
   - `prompt-pack.md`

## Commands

### A) Generate planning prompt (Stage 1)

```bash
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "<idea text>" \
  --title "<project title>" \
  --duration-sec 45 \
  --run-id <run-id>
```

This writes `planning.prompt.md`. Then let Claude generate plan JSON using that prompt.

### B) Parse and render with plan JSON (Stage 2)

```bash
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "<idea text>" \
  --title "<project title>" \
  --run-id <run-id> \
  --plan-json path/to/plan.json
```

or with markdown text containing a JSON code block:

```bash
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "<idea text>" \
  --title "<project title>" \
  --run-id <run-id> \
  --plan-text path/to/plan.md
```

## Design Principles

- Prefer **intent-first planning** over hardcoded shot templates.
- Keep output compact and creator-facing (timeline board + prompt pack).
- Let mode choice follow shot language:
  - `i2v` for clear cut-in opening composition
  - `keyframes` for continuous transition goals
  - `multiref` for identity/style consistency
  - `t2v` for direction-first ideation shots

## References

- Mode selection and timeline thinking: `references/mode-selection.md`
- Output artifact definitions: `references/output-artifacts.md`
