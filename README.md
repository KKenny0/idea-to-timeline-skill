# idea-to-timeline-skill

Standalone Claude Code skill project for converting a plain-text idea into:
- a creator-facing timeline story panel
- a reusable professional video prompt pack

## Structure

- `idea-to-timeline-panel/` — skill folder
  - `SKILL.md`
  - `scripts/`
  - `references/`
- `idea-to-timeline-panel.skill` — packaged distributable skill file

## Quick Verify (2-stage)

### 1) Generate planning prompt

```bash
cd idea-to-timeline-panel
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "社恐程序员为了白嫖自助餐误入相亲大会，最后反向圈粉" \
  --title "Standalone Verify" \
  --run-id standalone-verify
```

### 2) Prepare plan JSON and render panel

Create `plan.json` (Claude output), then run:

```bash
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "社恐程序员为了白嫖自助餐误入相亲大会，最后反向圈粉" \
  --title "Standalone Verify" \
  --run-id standalone-verify \
  --plan-json ./plan.json
```

Open:

```bash
open outputs/timeline-panel/standalone-verify/index.html
```
