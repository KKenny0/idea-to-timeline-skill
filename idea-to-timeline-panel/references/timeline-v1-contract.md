# timeline.v1 Contract (Practical)

## Required top-level keys

- `meta`
- `project`
- `assets`
- `shots`

## Shot constraints

- `shot_id`: unique per timeline (e.g., `S01`)
- `start_sec < end_sec`
- `duration_sec == end_sec - start_sec`
- no overlap with previous shot
- `seedance_plan.duration_sec` must be in `[4, 15]`

## Control-mode guidance

- `continuous` transition should prefer `keyframes` or `multiref`
- `cut` transition usually does not need `keyframes`

## Minimum shot fields used by the panel

- `shot_id`
- `start_sec`, `end_sec`, `duration_sec`
- `narrative_purpose`
- `scene`
- `action`
- `control_mode`
- `transition_to_next`
- `refs.image_asset_ids|video_asset_ids|audio_asset_ids`
- `prompt_cn`
- `negative_prompt`
- `seedance_plan.duration_sec`
