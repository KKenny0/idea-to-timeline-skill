# Output Artifacts (Simplified)

Each run writes to `outputs/timeline-panel/<run-id>/`.

## Core files for creators

Per variant output folder (e.g. `<run-id>/variant-01/` or `<run-id>/<plan-file-stem>/`):

- `timeline.story.json` — concise timeline story data
- `timeline.panel.json` — panel-oriented view model
- `panel.md` — readable timeline board
- `index.html` — clickable timeline board
- `prompt-pack.md` — reusable professional video prompt pack
- `seedance-execution.md` — long-video segment execution plan (Seedance 4-15s friendly, includes prompt + dialogue + SFX)

## Internal helper files

At run root (`<run-id>/`):

- `planning.prompt.variant-01.md` ... `planning.prompt.variant-03.md` — prompts for Claude planning stage
- `variants.manifest.json` — generated variant/style mapping
- `rendered.variants.json` — rendered outputs index

Per variant folder:

- `timeline.plan.json` — normalized plan parsed from Claude output

## Success criteria

Treat the run as successful when:

1. command exits with code `0`
2. at least one variant folder contains `index.html` with `Timeline Story Panel`
3. at least one variant folder contains `prompt-pack.md`
4. run root contains `rendered.variants.json`
