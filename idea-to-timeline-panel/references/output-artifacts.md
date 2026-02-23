# Output Artifacts (Simplified)

Each run writes to `outputs/timeline-panel/<run-id>/`.

## Core files for creators

- `timeline.story.json` — concise timeline story data
- `timeline.panel.json` — panel-oriented view model
- `panel.md` — readable timeline board
- `index.html` — clickable timeline board (same as `panel.html`)
- `prompt-pack.md` — reusable professional video prompt pack
- `seedance-execution.md` — long-video segment execution plan (Seedance 4-15s friendly)

## Internal helper files

- `planning.prompt.md` — prompt template for Claude planning stage
- `timeline.plan.json` — normalized plan parsed from Claude output

## Success criteria

Treat the run as successful when:

1. command exits with code `0`
2. `index.html` exists and contains `Timeline Story Panel`
3. `prompt-pack.md` exists and includes all shot ids
4. `seedance-execution.md` exists and includes at least one segment block
