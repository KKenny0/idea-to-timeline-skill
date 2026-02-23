# Planning JSON Contract (for Claude output)

Use this structure for Stage-1 planning output. Keep it compact.

```json
{
  "project": {
    "title": "",
    "idea": "",
    "target_duration_sec": 45,
    "aspect_ratio": "16:9"
  },
  "style": {
    "genre": "",
    "tone": "",
    "visual_style": ""
  },
  "shots": [
    {
      "id": "S01",
      "start": 0,
      "end": 8,
      "purpose": "",
      "scene": "",
      "action": "",
      "camera": "",
      "mode": "i2v",
      "transition": "cut",
      "prompt_video": "",
      "negative_prompt": "",
      "references": []
    }
  ]
}
```

## Notes

- `shots` should be ordered by timeline.
- `mode` options: `t2v | i2v | keyframes | multiref`.
- Do not add heavy internal fields unless needed.
- The parser accepts JSON inside markdown code fences.
