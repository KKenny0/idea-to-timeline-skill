#!/usr/bin/env python3
import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def normalize_shot(shot: Dict[str, Any], index: int) -> Dict[str, Any]:
    sid = shot.get("shot_id") or shot.get("id") or f"S{index:02d}"
    start = float(shot.get("start_sec", shot.get("start", 0)))
    end = float(shot.get("end_sec", shot.get("end", start + float(shot.get("duration_sec", 8)))))
    duration = max(0.0, end - start)

    prompt = shot.get("prompt_video") or shot.get("prompt_cn") or shot.get("prompt") or ""
    negative = shot.get("negative_prompt") or ""

    references = shot.get("references") or shot.get("refs", {}).get("image_asset_ids", []) or []
    if isinstance(references, str):
        references = [references]

    return {
        "shot_id": sid,
        "start_sec": start,
        "end_sec": end,
        "duration_sec": duration,
        "purpose": shot.get("purpose") or shot.get("narrative_purpose", ""),
        "scene": shot.get("scene", ""),
        "action": shot.get("action", ""),
        "camera": shot.get("camera", ""),
        "control_mode": shot.get("control_mode") or shot.get("mode", "i2v"),
        "transition_to_next": shot.get("transition_to_next") or shot.get("transition", "cut"),
        "prompt_video": prompt,
        "negative_prompt": negative,
        "references": references,
    }


def build_timeline_story(plan: Dict[str, Any]) -> Dict[str, Any]:
    project = plan.get("project", {})
    style = plan.get("style", {})
    shots = [normalize_shot(shot, i) for i, shot in enumerate(plan.get("shots", []), start=1)]

    target_duration = project.get("target_duration_sec")
    if target_duration is None and shots:
        target_duration = max(s["end_sec"] for s in shots)

    return {
        "meta": {
            "schema": "timeline.story.v2",
            "generated_at": now_iso(),
        },
        "project": {
            "title": project.get("title", "Untitled"),
            "idea": project.get("idea", ""),
            "target_duration_sec": target_duration,
            "aspect_ratio": project.get("aspect_ratio", "16:9"),
        },
        "style": {
            "genre": style.get("genre", ""),
            "tone": style.get("tone", ""),
            "visual_style": style.get("visual_style", ""),
        },
        "shots": shots,
    }


def build_timeline_view(story: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "meta": {
            "schema": "timeline.panel.v2",
            "generated_at": now_iso(),
            "source_schema": story.get("meta", {}).get("schema"),
        },
        "project": story.get("project", {}),
        "style": story.get("style", {}),
        "summary": {
            "shot_count": len(story.get("shots", [])),
            "target_duration_sec": story.get("project", {}).get("target_duration_sec"),
        },
        "shots": story.get("shots", []),
    }


def render_prompt_pack(story: Dict[str, Any]) -> str:
    lines: List[str] = [
        "# Professional Video Prompt Pack",
        "",
        f"- Project: {story['project'].get('title', 'Untitled')}",
        f"- Idea: {story['project'].get('idea', '')}",
        f"- Aspect Ratio: {story['project'].get('aspect_ratio', '16:9')}",
        "",
    ]

    for shot in story.get("shots", []):
        lines.append(f"## {shot['shot_id']} ({shot['start_sec']}s-{shot['end_sec']}s)")
        lines.append(f"- Mode: `{shot['control_mode']}`")
        lines.append(f"- Transition: `{shot['transition_to_next']}`")
        if shot.get("camera"):
            lines.append(f"- Camera: {shot['camera']}")
        if shot.get("references"):
            lines.append(f"- References: {', '.join(str(x) for x in shot['references'])}")
        lines.append(f"- Prompt: {shot.get('prompt_video', '')}")
        if shot.get("negative_prompt"):
            lines.append(f"- Negative Prompt: {shot['negative_prompt']}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def render_panel_markdown(view: Dict[str, Any]) -> str:
    project = view.get("project", {})
    style = view.get("style", {})

    lines: List[str] = [
        "# Timeline Story Panel",
        "",
        f"- Project: **{project.get('title', 'Untitled')}**",
        f"- Idea: {project.get('idea', '')}",
        f"- Duration: {project.get('target_duration_sec', '?')}s",
        f"- Style: {style.get('genre', '')} | {style.get('tone', '')} | {style.get('visual_style', '')}",
        f"- Generated At: {view['meta']['generated_at']}",
        "",
        "## Shot Board",
        "",
    ]

    for shot in view.get("shots", []):
        lines.append(f"### {shot['shot_id']} | {shot['start_sec']}s - {shot['end_sec']}s")
        lines.append(f"- Purpose: {shot.get('purpose', '')}")
        lines.append(f"- Scene/Action: {shot.get('scene', '')} / {shot.get('action', '')}")
        lines.append(f"- Camera: {shot.get('camera', '')}")
        lines.append(f"- Mode / Transition: `{shot.get('control_mode', '')}` / `{shot.get('transition_to_next', '')}`")
        lines.append(f"- Prompt: {shot.get('prompt_video', '')}")
        if shot.get("negative_prompt"):
            lines.append(f"- Negative: {shot['negative_prompt']}")
        if shot.get("references"):
            lines.append(f"- References: {', '.join(str(x) for x in shot['references'])}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def render_panel_html(view: Dict[str, Any]) -> str:
    project = view.get("project", {})
    style = view.get("style", {})

    cards: List[str] = []
    for shot in view.get("shots", []):
        refs = shot.get("references") or []
        refs_text = ", ".join(str(r) for r in refs) if refs else "-"
        cards.append(
            "\n".join(
                [
                    f'<section class="card">',
                    f'  <div class="head"><h3>{html.escape(shot["shot_id"])}</h3><span>{html.escape(str(shot["start_sec"]))}s - {html.escape(str(shot["end_sec"]))}s</span></div>',
                    f'  <p><strong>Purpose:</strong> {html.escape(str(shot.get("purpose", "")))}</p>',
                    f'  <p><strong>Scene/Action:</strong> {html.escape(str(shot.get("scene", "")))} / {html.escape(str(shot.get("action", "")))}</p>',
                    f'  <p><strong>Camera:</strong> {html.escape(str(shot.get("camera", "")))}</p>',
                    f'  <p><strong>Mode / Transition:</strong> <code>{html.escape(str(shot.get("control_mode", "")))}</code> / <code>{html.escape(str(shot.get("transition_to_next", "")))}</code></p>',
                    f'  <details><summary>Prompt</summary><p>{html.escape(str(shot.get("prompt_video", "")))}</p></details>',
                    f'  <p><strong>Negative:</strong> {html.escape(str(shot.get("negative_prompt", "-")))}</p>',
                    f'  <p><strong>References:</strong> {html.escape(refs_text)}</p>',
                    f'</section>',
                ]
            )
        )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Timeline Story Panel - {html.escape(project.get('title', 'Untitled'))}</title>
  <style>
    :root {{ --bg:#0b1020; --fg:#e8ecff; --card:#151b33; --line:#2a355f; --muted:#9fb0e0; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; background:var(--bg); color:var(--fg); }}
    .wrap {{ max-width:1100px; margin:0 auto; padding:24px; }}
    .meta, .card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; }}
    .meta {{ padding:14px; margin-bottom:14px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:12px; }}
    .card {{ padding:14px; }}
    .head {{ display:flex; justify-content:space-between; align-items:center; gap:12px; }}
    .head span {{ color:var(--muted); font-size:12px; }}
    code {{ background:#1a2449; border:1px solid var(--line); padding:1px 6px; border-radius:6px; }}
  </style>
</head>
<body>
  <main class=\"wrap\">
    <h1>Timeline Story Panel</h1>
    <section class=\"meta\">
      <p><strong>Project:</strong> {html.escape(project.get('title', 'Untitled'))}</p>
      <p><strong>Idea:</strong> {html.escape(project.get('idea', ''))}</p>
      <p><strong>Duration:</strong> {html.escape(str(project.get('target_duration_sec', '?')))}s</p>
      <p><strong>Style:</strong> {html.escape(style.get('genre', ''))} | {html.escape(style.get('tone', ''))} | {html.escape(style.get('visual_style', ''))}</p>
      <p><strong>Generated At:</strong> {html.escape(view['meta']['generated_at'])}</p>
    </section>
    <section class=\"grid\">{''.join(cards)}</section>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render timeline panel and prompt pack from shot plan JSON")
    parser.add_argument("--plan", required=True, help="Path to normalized plan JSON")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    args = parser.parse_args()

    plan_path = Path(args.plan).resolve()
    out_dir = Path(args.out_dir).resolve()

    plan = read_json(plan_path)
    story = build_timeline_story(plan)
    view = build_timeline_view(story)

    write_json(out_dir / "timeline.story.json", story)
    write_json(out_dir / "timeline.panel.json", view)
    write_text(out_dir / "panel.md", render_panel_markdown(view))

    panel_html = render_panel_html(view)
    write_text(out_dir / "panel.html", panel_html)
    write_text(out_dir / "index.html", panel_html)
    write_text(out_dir / "prompt-pack.md", render_prompt_pack(story))

    print(f"Panel generated at: {out_dir}")
    print(f"Open this file in browser: {out_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
