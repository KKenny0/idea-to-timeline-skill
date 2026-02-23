# Seedance Platform Spec (Practical Reference)

Use this reference when writing planning prompts and execution guidance.

## Input constraints

- Images: jpeg/png/webp/bmp/tiff/gif, up to 9, each <30MB
- Videos: mp4/mov, up to 3, total length 2-15s, each <50MB, resolution 480p-720p
- Audios: mp3/wav, up to 3, total length <=15s, each <15MB
- Total files: up to 12 (image+video+audio)

## Generation constraints

- Single generation duration: 4-15s recommended
- For >15s videos: split into multiple segments and stitch with video extension
- Prompt supports multimodal references via `@图片N` / `@视频N` / `@音频N`

## Prompt best practices

- Use timestamped timeline prompts for 13-15s segments
- Keep dialogue and sound effects explicit
- Add forbidden items at end (watermark/subtitle/logo/artifact)
- For continuity-heavy sequence, prefer same-subject same-space planning

## Safety/content reminders

- Avoid realistic human-face upload materials if platform blocks them
- Keep references stylistically consistent to reduce drift

## Source

- https://github.com/songguoxs/seedance-prompt-skill/blob/master/README_zh.md
