#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

STYLE_PRESETS = [
    {
        "name": "cinematic-realism",
        "label": "电影写实",
        "genre": "现实电影",
        "tone": "克制、沉浸",
        "visual_style": "电影级写实光影",
    },
    {
        "name": "stylized-animation",
        "label": "风格化动画",
        "genre": "动画叙事",
        "tone": "夸张、节奏强",
        "visual_style": "高饱和风格化动画",
    },
    {
        "name": "commercial-short",
        "label": "广告短片",
        "genre": "品牌广告",
        "tone": "强记忆点、快节奏",
        "visual_style": "高级商业质感",
    },
]


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
                "dialogue": shot.get("dialogue", ""),
                "sfx": shot.get("sfx", ""),
                "mode": shot.get("mode", shot.get("control_mode", "i2v")),
                "transition": shot.get("transition", shot.get("transition_to_next", "cut")),
                "prompt_video": shot.get("prompt_video") or shot.get("prompt") or "",
                "negative_prompt": shot.get("negative_prompt", ""),
                "references": refs,
            }
        )

    normalized_shots.sort(key=lambda x: x["start_sec"])

    forbidden_items = project.get("forbidden_items") or ["水印", "字幕", "Logo", "畸形肢体", "面部漂移"]

    return {
        "project": {
            "title": project.get("title", title),
            "idea": project.get("idea", idea),
            "target_duration_sec": project.get("target_duration_sec", duration_sec),
            "aspect_ratio": project.get("aspect_ratio", "16:9"),
            "forbidden_items": forbidden_items,
        },
        "style": {
            "genre": style.get("genre", ""),
            "tone": style.get("tone", ""),
            "visual_style": style.get("visual_style", ""),
            "fps": style.get("fps", 24),
        },
        "shots": normalized_shots,
    }


def resolve_variant_specs(variant_count: int, variant_labels: str) -> List[Dict[str, str]]:
    count = max(1, min(3, variant_count))

    if variant_labels.strip():
        labels = [x.strip() for x in variant_labels.split(",") if x.strip()]
        if labels:
            return [
                {
                    "id": f"variant-{i:02d}",
                    "label": labels[i - 1] if i - 1 < len(labels) else labels[-1],
                    "genre": "",
                    "tone": "",
                    "visual_style": "",
                }
                for i in range(1, count + 1)
            ]

    picked = STYLE_PRESETS[:count]
    return [
        {
            "id": f"variant-{i:02d}",
            "label": preset["label"],
            "genre": preset["genre"],
            "tone": preset["tone"],
            "visual_style": preset["visual_style"],
        }
        for i, preset in enumerate(picked, start=1)
    ]


def build_planning_prompt(idea: str, title: str, duration_sec: int, variant: Dict[str, str]) -> str:
    style_hint = f"风格锚点：{variant['label']}"
    if variant.get("genre") or variant.get("tone") or variant.get("visual_style"):
        style_hint += f"；genre={variant.get('genre','')}；tone={variant.get('tone','')}；visual_style={variant.get('visual_style','')}"

    return f"""# Idea-to-Timeline Planning Prompt (Seedance-oriented)

你是专业的视频分镜策划 + Seedance 提示词工程助手。
请基于用户 idea 直接生成 **JSON**（不要解释文字）。

## 方案信息
- variant_id: {variant['id']}
- variant_style: {style_hint}

## 用户输入
- title: {title}
- idea: {idea}
- target_duration_sec: {duration_sec}

## 规划原则（借鉴 Seedance 工作流）
1. 先定剪辑语法：镜头是“切”还是“连续推进”。
2. 再选控制模式：
   - `i2v`：开场构图锁定、适合 hard cut
   - `keyframes`：A→B 连续过渡
   - `multiref`：角色/服装/道具一致性
   - `t2v`：方向探索与氛围段落
3. 每个镜头都输出可直接用于 Seedance 的 `prompt_video`。
4. 超过 15 秒时，按时间线合理拆分镜头（脚本会进一步按 15 秒段输出执行方案）。
5. 结尾始终带禁止项，避免水印/字幕/Logo/畸形等问题。

## 输出 JSON 结构（必须严格遵循）
```json
{{
  "project": {{
    "title": "{title}",
    "idea": "{idea}",
    "target_duration_sec": {duration_sec},
    "aspect_ratio": "16:9",
    "forbidden_items": ["水印", "字幕", "Logo", "畸形肢体", "面部漂移"]
  }},
  "style": {{
    "genre": "{variant.get('genre','')}",
    "tone": "{variant.get('tone','')}",
    "visual_style": "{variant.get('visual_style','')}",
    "fps": 24
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
      "dialogue": "",
      "sfx": "",
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


def generate_variant_prompts(out_dir: Path, idea: str, title: str, duration_sec: int, variants: List[Dict[str, str]]) -> None:
    prompt_paths: List[Dict[str, str]] = []
    for variant in variants:
        prompt = build_planning_prompt(idea, title, duration_sec, variant)
        prompt_path = out_dir / f"planning.prompt.{variant['id']}.md"
        write_text(prompt_path, prompt)
        prompt_paths.append({"variant_id": variant["id"], "style": variant["label"], "prompt_path": str(prompt_path)})

    manifest = {
        "project": {"title": title, "idea": idea, "target_duration_sec": duration_sec},
        "variants": prompt_paths,
    }
    write_json(out_dir / "variants.manifest.json", manifest)


def collect_plan_inputs(args: argparse.Namespace, out_dir: Path) -> List[Tuple[str, Path, str]]:
    plans: List[Tuple[str, Path, str]] = []  # (variant_id, path, mode)

    if args.plan_json:
        plans.append(("variant-01", Path(args.plan_json).resolve(), "json"))
    if args.plan_text:
        plans.append(("variant-01", Path(args.plan_text).resolve(), "text"))

    if args.plans_dir:
        plans_dir = Path(args.plans_dir).resolve()
        for p in sorted(plans_dir.glob("*.json")):
            plans.append((p.stem, p, "json"))
        for p in sorted(plans_dir.glob("*.md")):
            plans.append((p.stem, p, "text"))

    # also support default place: out_dir/plans/*.json|*.md
    default_plans_dir = out_dir / "plans"
    if not plans and default_plans_dir.exists():
        for p in sorted(default_plans_dir.glob("*.json")):
            plans.append((p.stem, p, "json"))
        for p in sorted(default_plans_dir.glob("*.md")):
            plans.append((p.stem, p, "text"))

    return plans


def main() -> int:
    parser = argparse.ArgumentParser(description="Idea -> timeline panel pipeline (LLM-output first)")
    parser.add_argument("--idea", required=True, help="User idea text")
    parser.add_argument("--title", default="Idea Timeline Panel", help="Project title")
    parser.add_argument("--duration-sec", type=int, default=45, help="Target duration in seconds")
    parser.add_argument("--run-id", default=None, help="Run id under output root")
    parser.add_argument("--output-root", default="outputs/timeline-panel", help="Directory root for outputs")

    parser.add_argument("--variant-count", type=int, default=1, help="How many alternative storyboard variants to generate prompts for (1-3)")
    parser.add_argument("--variant-labels", default="", help="Comma-separated custom labels for variants")

    parser.add_argument("--plan-json", default=None, help="Path to a single plan JSON file generated by Claude")
    parser.add_argument("--plan-text", default=None, help="Path to a single plan text/markdown containing JSON block")
    parser.add_argument("--plans-dir", default=None, help="Directory containing multiple plan files (*.json/*.md), each treated as one variant")
    args = parser.parse_args()

    run_id = args.run_id or f"idea-{slugify(args.title)}"
    out_dir = Path(args.output_root).resolve() / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    variants = resolve_variant_specs(args.variant_count, args.variant_labels)
    generate_variant_prompts(out_dir, args.idea, args.title, args.duration_sec, variants)

    plans = collect_plan_inputs(args, out_dir)
    if not plans:
        print(f"Generated {len(variants)} planning prompts at: {out_dir}")
        print("Next step: let Claude produce plan files (json/md) for each variant, put them in --plans-dir or outputs/.../plans/, then rerun.")
        return 0

    panel_script = Path(__file__).resolve().parent / "timeline_panel_v1.py"

    rendered: List[Dict[str, str]] = []
    for variant_id, plan_path, mode in plans:
        if mode == "json":
            raw_plan = read_json(plan_path)
        else:
            raw_text = plan_path.read_text(encoding="utf-8")
            raw_plan = extract_json_block(raw_text)

        normalized_plan = normalize_plan(raw_plan, args.idea, args.title, args.duration_sec)
        variant_out = out_dir / variant_id
        normalized_path = variant_out / "timeline.plan.json"
        write_json(normalized_path, normalized_plan)

        cmd = [
            "python3",
            str(panel_script),
            "--plan",
            str(normalized_path),
            "--out-dir",
            str(variant_out),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            return result.returncode

        rendered.append(
            {
                "variant_id": variant_id,
                "plan_source": str(plan_path),
                "output_dir": str(variant_out),
                "index_html": str(variant_out / "index.html"),
            }
        )

    write_json(out_dir / "rendered.variants.json", {"run_id": run_id, "variants": rendered})

    print(f"Rendered {len(rendered)} variant(s). Root: {out_dir}")
    for item in rendered:
        print(f"- {item['variant_id']}: {item['index_html']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
