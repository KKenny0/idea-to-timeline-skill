# idea-to-timeline-skill

Standalone Claude Code skill project for converting a plain-text idea into:
- timeline JSON artifacts
- validation report
- clickable HTML timeline creator panel

## Structure

- `idea-to-timeline-panel/` — actual skill folder
  - `SKILL.md`
  - `scripts/`
  - `references/`
- `idea-to-timeline-panel.skill` — packaged distributable skill file

## Quick Verify

```bash
cd idea-to-timeline-panel
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "社恐程序员为了白嫖自助餐误入相亲大会，最后反向圈粉" \
  --title "Standalone Verify" \
  --run-id standalone-verify
```

Open:

```bash
open outputs/timeline-panel/standalone-verify/index.html
```
