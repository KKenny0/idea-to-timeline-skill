# idea-to-timeline-skill

Standalone Claude Code skill project for converting a plain-text idea into:
- a creator-facing timeline story panel
- a reusable professional video prompt pack
- 2-3 alternative storyboard variants (same idea, different style)

## Structure

- `idea-to-timeline-panel/` — skill folder
  - `SKILL.md`
  - `scripts/`
  - `references/`
- `idea-to-timeline-panel.skill` — packaged distributable skill file

## Quick Verify (multi-variant 2-stage)

### 1) Generate 2-3 planning prompts

```bash
cd idea-to-timeline-panel
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "社恐程序员为了白嫖自助餐误入相亲大会，最后反向圈粉" \
  --title "Standalone Verify" \
  --run-id standalone-verify \
  --variant-count 3
```

This creates:
- `outputs/timeline-panel/standalone-verify/planning.prompt.variant-01.md`
- `...variant-02.md`
- `...variant-03.md`
- `variants.manifest.json`

### 2) Put Claude plans in a folder and render all variants

Create a directory like:

```text
outputs/timeline-panel/standalone-verify/plans/
  - cinematic.json
  - animation.json
  - commercial.md
```

Then run:

```bash
python3 scripts/idea_to_timeline_pipeline_v1.py \
  --idea "社恐程序员为了白嫖自助餐误入相亲大会，最后反向圈粉" \
  --title "Standalone Verify" \
  --run-id standalone-verify \
  --plans-dir outputs/timeline-panel/standalone-verify/plans
```

### 3) Review outputs

- Variant index: `outputs/timeline-panel/standalone-verify/rendered.variants.json`
- One variant panel: `outputs/timeline-panel/standalone-verify/cinematic/index.html`
