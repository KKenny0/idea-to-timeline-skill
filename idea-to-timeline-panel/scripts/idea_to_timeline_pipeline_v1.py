#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def slugify(text: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in text.strip())
    while "--" in clean:
        clean = clean.replace("--", "-")
    return clean.strip("-")[:48] or "idea"


def extract_json_block(text: str) -> Dict[str, Any]:
    fenced = re.findall(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    if fenced:
        return json.loads(fenced[0])

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return json.loads(text[first_brace : last_brace + 1])

    raise ValueError("No JSON object found in plan text")


def normalize_plan(raw: Dict[str, Any], idea: str, title: str, duration_sec: int) -> Dict[str, Any]:
    project = raw.get("project", {})
    style = raw.get("style", {})
    shots_in = raw.get("shots", [])

    normalized_shots: List[Dict[str, Any]] = []
    last_end = 0.0
    for i, shot in enumerate(shots_in, start=1):
        sid = shot.get("shot_id") or shot.get("id") or f"S{i:02d}"
        start = float(shot.get("start_sec", shot.get("start", last_end)))

        if "end_sec" in shot or "end" in shot:
            end = float(shot.get("end_sec", shot.get("end")))
        else:
            dur = float(shot.get("duration_sec", shot.get("duration", 8)))
            end = start + max(1.0, dur)

        if end <= start:
            end = start + 1.0

        last_end = end

        refs = shot.get("references") or []
        if isinstance(refs, str):
            refs = [refs]

        normalized_shots.append(
            {
                "shot_id": sid,
                "start_sec": round(start, 2),
                "end_sec": round(end, 2),
                "purpose": shot.get("purpose", ""),
                "scene": shot.get("scene", ""),
                "action": shot.get("action", ""),
                "camera": shot.get("camera", ""),
                "mode": shot.get("mode", shot.get("control_mode", "i2v")),
                "transition": shot.get("transition", shot.get("transition_to_next", "cut")),
                "prompt_video": shot.get("prompt_video") or shot.get("prompt") or "",
                "negative_prompt": shot.get("negative_prompt", ""),
                "references": refs,
            }
        )

    return {
        "project": {
            "title": project.get("title", title),
            "idea": project.get("idea", idea),
            "target_duration_sec": project.get("target_duration_sec", duration_sec),
            "aspect_ratio": project.get("aspect_ratio", "16:9"),
        },
        "style": {
            "genre": style.get("genre", ""),
            "tone": style.get("tone", ""),
            "visual_style": style.get("visual_style", ""),
        },
        "shots": normalized_shots,
    }


def build_planning_prompt(idea: str, title: str, duration_sec: int) -> str:
    return f"""# Idea-to-Timeline Planning Prompt

你是视频分镜策划助手。请基于用户 idea 直接生成 **JSON**（不要解释文字）。

## 用户输入
- title: {title}
- idea: {idea}
- target_duration_sec: {duration_sec}

## 产出要求
1. 先考虑叙事结构（铺垫/冲突/反转/收束）和时间线。
2. 每个镜头都要给可直接复用的视频生成提示词 `prompt_video`。
3. 模式 `mode` 在以下值内选择：`t2v` / `i2v` / `keyframes` / `multiref`。
4. 结构尽量简洁，不要输出无关字段。

## 输出 JSON 结构（必须严格遵循）
```json
{{
  "project": {{
    "title": "{title}",
    "idea": "{idea}",
    "target_duration_sec": {duration_sec},
    "aspect_ratio": "16:9"
  }},
  "style": {{
    "genre": "",
    "tone": "",
    "visual_style": ""
  }},
  "shots": [
    {{
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
    }}
  ]
}}
```
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Idea -> timeline panel pipeline (LLM-output first)")
    parser.add_argument("--idea", required=True, help="User idea text")
    parser.add_argument("--title", default="Idea Timeline Panel", help="Project title")
    parser.add_argument("--duration-sec", type=int, default=45, help="Target duration in seconds")
    parser.add_argument("--run-id", default=None, help="Run id under output root")
    parser.add_argument("--output-root", default="outputs/timeline-panel", help="Directory root for outputs")
    parser.add_argument("--plan-json", default=None, help="Path to plan JSON file generated by Claude")
    parser.add_argument("--plan-text", default=None, help="Path to plan text/markdown containing JSON block")
    args = parser.parse_args()

    run_id = args.run_id or f"idea-{slugify(args.title)}"
    out_dir = Path(args.output_root).resolve() / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    planning_prompt = build_planning_prompt(args.idea, args.title, args.duration_sec)
    write_text(out_dir / "planning.prompt.md", planning_prompt)

    if not args.plan_json and not args.plan_text:
        print(f"Planning prompt generated at: {out_dir / 'planning.prompt.md'}")
        print("Next step: let Claude generate plan JSON, save it, then rerun with --plan-json or --plan-text")
        return 0

    if args.plan_json:
        raw_plan = read_json(Path(args.plan_json).resolve())
    else:
        raw_text = Path(args.plan_text).resolve().read_text(encoding="utf-8")
        raw_plan = extract_json_block(raw_text)

    normalized_plan = normalize_plan(raw_plan, args.idea, args.title, args.duration_sec)
    normalized_path = out_dir / "timeline.plan.json"
    write_json(normalized_path, normalized_plan)

    panel_script = Path(__file__).resolve().parent / "timeline_panel_v1.py"
    cmd = [
        "python3",
        str(panel_script),
        "--plan",
        str(normalized_path),
        "--out-dir",
        str(out_dir),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        return result.returncode

    if result.stdout.strip():
        print(result.stdout.strip())
    print(f"Pipeline completed. Open: {out_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
