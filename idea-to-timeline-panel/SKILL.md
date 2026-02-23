---
name: idea-to-timeline-panel
description: Turn a raw video idea/logline into a practical timeline story panel and reusable professional Seedance-ready video prompts. Use when a user asks for storyboard planning, shot timeline design, mode selection (t2v/i2v/keyframes/multiref), creator-facing panel export, long-video segmented execution planning for durations over 15 seconds, or prompt-pack generation from an initial concept.
---

# Idea To Timeline Panel

Use a two-stage flow: **Claude plans first**, scripts parse and render after.

## Workflow

1. Read user idea and target duration.
2. Make Claude output a compact JSON shot plan (or markdown containing a JSON block).
3. Parse that output into `timeline.plan.json`.
4. Render creator artifacts (single variant or multi-variant):
   - `timeline.story.json`
   - `timeline.panel.json`
   - `panel.md`
   - `index.html`
   - `prompt-pack.md`
   - `seedance-execution.md`
   - `rendered.variants.json` (when multi-variant is enabled)

## Commands

### A) Generate planning prompts (Stage 1)

```bash
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "<idea text>" \
  --title "<project title>" \
  --duration-sec 45 \
  --run-id <run-id> \
  --variant-count 3
```

This writes `planning.prompt.variant-01.md` ... `planning.prompt.variant-03.md` and `variants.manifest.json`. Then let Claude generate plan JSON/MD for each variant.

### B) Parse and render (Stage 2)

Single plan (输出目录名取 `plan` 文件名，如 `my-plan.json` -> `<run-id>/my-plan/`):

```bash
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "<idea text>" \
  --title "<project title>" \
  --run-id <run-id> \
  --plan-json path/to/my-plan.json
```

或者用 markdown(JSON 代码块) 作为单方案输入：

```bash
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "<idea text>" \
  --title "<project title>" \
  --run-id <run-id> \
  --plan-text path/to/my-plan.md
```

Multiple alternatives (recommended for 2-3 storyboard options):

```bash
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "<idea text>" \
  --title "<project title>" \
  --run-id <run-id> \
  --plans-dir path/to/plans
```

`plans-dir` can contain mixed `*.json` and `*.md` files. Each file becomes one variant output folder.

Notes:
- Do not mix `--plans-dir` with `--plan-json` / `--plan-text` in the same run.
- If `--plans-dir` is omitted, the script will auto-read `outputs/timeline-panel/<run-id>/plans/` when that folder exists.

## Design Principles

- Prefer **intent-first planning** over hardcoded shot templates.
- Keep output compact and creator-facing (timeline board + prompt pack + execution plan).
- Keep mode choice aligned with shot language:
  - `i2v` for clear cut-in opening composition
  - `keyframes` for continuous transition goals
  - `multiref` for identity/style consistency
  - `t2v` for direction-first ideation shots
- For long videos, output segmented execution guidance (Seedance-friendly 4-15s chunks).

## References

- Mode selection and timeline thinking: `references/mode-selection.md`
- Seedance platform specs and constraints: `references/seedance-platform-spec.md`
- Output artifact definitions: `references/output-artifacts.md`
