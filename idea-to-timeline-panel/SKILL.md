---
name: idea-to-timeline-panel
description: Convert a plain-text story idea into a production-ready timeline execution pack and clickable HTML creator panel. Use when a user asks to go from “idea/concept/logline” to shot-by-shot timeline planning, validation, prompt pack generation, asset checklist generation, or an openable index.html panel for review/export.
---

# Idea To Timeline Panel

Generate a deterministic timeline pack from a single idea, then render a creator-friendly HTML board for execution review.

## Quick Start

1. Run the pipeline script:

```bash
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "社恐程序员为了白嫖自助餐误入相亲大会，最后反向圈粉" \
  --title "Kenny Social Anxiety Dating Event" \
  --run-id idea-kenny-standalone
```

2. Open the generated panel:

```bash
open outputs/timeline-panel/idea-kenny-standalone/index.html
```

## Workflow

1. Parse user idea and metadata.
2. Build a 5-shot deterministic `timeline.v1` scaffold.
3. Validate temporal and control-mode constraints.
4. Export execution artifacts:
   - `timeline.input.v1.json`
   - `timeline.v1.json`
   - `timeline.view.v1.json`
   - `validation.report.json`
   - `panel.md`
   - `panel.html`
   - `index.html`
   - `asset-checklist.md`
   - `shot-prompt-pack.md`

## Commands

### A) End-to-end (recommended)

```bash
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "<idea text>" \
  --title "<project title>" \
  --run-id <optional-run-id> \
  --duration-sec 45 \
  --output-root outputs/timeline-panel
```

### B) Render panel from an existing timeline JSON

```bash
python3 scripts/timeline_panel_v1.py \
  --timeline path/to/timeline.v1.json \
  --out-dir outputs/timeline-panel/custom-run
```

## Editing Rules

- Keep `description` in frontmatter explicit about trigger phrases (idea/logline/timeline/panel/export).
- Keep SKILL.md concise; put detailed contracts in `references/`.
- Validate every script change by running at least one full end-to-end sample.
- If validation fails (`error_count > 0`), fix timeline fields before claiming completion.

## References

- Timeline contract and field map: `references/timeline-v1-contract.md`
- Output artifact descriptions: `references/output-artifacts.md`
