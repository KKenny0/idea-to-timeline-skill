# Output Artifacts

For each run, the skill writes to `outputs/timeline-panel/<run-id>/` (or custom `--output-root`):

- `timeline.input.v1.json`: deterministic planner output before panel rendering
- `timeline.v1.json`: canonical timeline used for execution
- `timeline.view.v1.json`: enriched view model for creator review
- `validation.report.json`: error/warning report and `valid` flag
- `panel.md`: text review board
- `panel.html`: HTML board
- `index.html`: same as `panel.html` for direct opening
- `asset-checklist.md`: registered and missing assets
- `shot-prompt-pack.md`: shot-by-shot prompt bundle

## Completion criteria

Treat run as successful when:

1. script exits with code `0`
2. `validation.report.json` has `valid=true`
3. `index.html` exists and contains `Timeline Creator Panel`
