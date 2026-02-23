#!/usr/bin/env python3
import argparse
import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class ValidationIssue:
    level: str
    code: str
    shot_id: str
    message: str


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


def index_assets(timeline: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    assets = timeline.get("assets", {})
    idx: Dict[str, Dict[str, Any]] = {}
    for kind in ("images", "videos", "audios"):
        for asset in assets.get(kind, []):
            idx[asset["asset_id"]] = asset
    return idx


def validate_timeline(timeline: Dict[str, Any]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    shots = timeline.get("shots", [])
    if not shots:
        issues.append(ValidationIssue("error", "NO_SHOTS", "GLOBAL", "timeline contains no shots"))
        return issues

    last_end = -1.0
    for shot in shots:
        sid = shot.get("shot_id", "UNKNOWN")
        start = float(shot.get("start_sec", 0))
        end = float(shot.get("end_sec", 0))
        duration = float(shot.get("duration_sec", 0))

        if end <= start:
            issues.append(ValidationIssue("error", "TIME_RANGE_INVALID", sid, "end_sec must be > start_sec"))
        if abs((end - start) - duration) > 1e-6:
            issues.append(ValidationIssue("error", "DURATION_MISMATCH", sid, "duration_sec must equal end_sec-start_sec"))
        if start < last_end:
            issues.append(ValidationIssue("error", "SHOT_OVERLAP", sid, "shot overlaps with previous shot"))
        last_end = end

        sd_duration = float(shot.get("seedance_plan", {}).get("duration_sec", 0))
        if sd_duration < 4 or sd_duration > 15:
            issues.append(ValidationIssue("error", "SEEDANCE_DURATION_RANGE", sid, "seedance duration must be in [4,15]"))

        transition = shot.get("transition_to_next")
        mode = shot.get("control_mode")
        if transition == "continuous" and mode not in {"keyframes", "multiref"}:
            issues.append(ValidationIssue("warning", "MODE_TRANSITION_MISMATCH", sid, "continuous transition usually expects keyframes/multiref"))
        if transition == "cut" and mode == "keyframes":
            issues.append(ValidationIssue("warning", "MODE_TRANSITION_MISMATCH", sid, "cut transition usually does not need keyframes"))

    return issues


def infer_mode_reason(shot: Dict[str, Any]) -> str:
    mode = shot.get("control_mode")
    if mode == "keyframes":
        return "Use keyframes to preserve continuous action and subject consistency across adjacent shots."
    if mode == "i2v":
        return "Use i2v to lock opening composition for clean entry into new setup or scene."
    if mode == "multiref":
        return "Use multiref to reinforce character and scene consistency with explicit references."
    if mode == "t2v":
        return "Use t2v for direction-first generation when shot priority is narrative intent."
    return "Mode selected by router policy."


def infer_risk_flags(shot: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    mode = shot.get("control_mode")
    transition = shot.get("transition_to_next")
    duration = float(shot.get("duration_sec", 0))

    if mode in {"t2v", "i2v"}:
        flags.append("character_consistency_risk")
    if transition == "continuous":
        flags.append("motion_continuity_risk")
    if duration >= 10:
        flags.append("long_shot_stability_risk")

    return flags


def infer_execution_hint(shot: Dict[str, Any]) -> Dict[str, str]:
    transition = shot.get("transition_to_next")
    if transition == "cut":
        return {"run_mode": "parallelizable", "note": "Can run in parallel with other cut shots if assets are ready."}
    if transition == "continuous":
        return {"run_mode": "sequential", "note": "Keep sequence with neighboring shots to preserve continuity."}
    return {"run_mode": "sequential", "note": "Default to sequential execution."}


def build_timeline_view(timeline: Dict[str, Any], asset_idx: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    view: Dict[str, Any] = {
        "meta": {
            "schema": "timeline.view.v1",
            "generated_at": now_iso(),
            "source_schema": timeline.get("meta", {}).get("schema", "timeline.v1"),
        },
        "project": timeline.get("project", {}),
        "summary": {
            "shot_count": len(timeline.get("shots", [])),
            "target_duration_sec": timeline.get("project", {}).get("target_duration_sec"),
        },
        "shots": [],
    }

    for idx, shot in enumerate(timeline.get("shots", []), start=1):
        refs = shot.get("refs", {})
        ref_ids = refs.get("image_asset_ids", []) + refs.get("video_asset_ids", []) + refs.get("audio_asset_ids", [])
        missing = [rid for rid in ref_ids if rid not in asset_idx]

        view["shots"].append(
            {
                "index": idx,
                "shot_id": shot.get("shot_id"),
                "time_range": f"{shot.get('start_sec')}s - {shot.get('end_sec')}s",
                "narrative_purpose": shot.get("narrative_purpose"),
                "scene": shot.get("scene"),
                "action": shot.get("action"),
                "control_mode": shot.get("control_mode"),
                "transition_to_next": shot.get("transition_to_next"),
                "mode_reason": infer_mode_reason(shot),
                "risk_flags": infer_risk_flags(shot),
                "execution_hint": infer_execution_hint(shot),
                "missing_assets": missing,
                "prompt_cn": shot.get("prompt_cn", ""),
                "negative_prompt": shot.get("negative_prompt", ""),
            }
        )

    return view


def render_panel_markdown(timeline: Dict[str, Any], view: Dict[str, Any], issues: List[ValidationIssue]) -> str:
    project = timeline.get("project", {})
    errors = [i for i in issues if i.level == "error"]
    warnings = [i for i in issues if i.level == "warning"]

    lines: List[str] = [
        "# Timeline Creator Panel (v1)",
        "",
        f"- Project: **{project.get('title', 'Untitled')}**",
        f"- Idea: {project.get('idea', '')}",
        f"- Target Duration: {project.get('target_duration_sec', '?')}s",
        f"- Generated At: {view['meta']['generated_at']}",
        "",
        "## Validation Summary",
        f"- Errors: **{len(errors)}**",
        f"- Warnings: **{len(warnings)}**",
    ]

    if issues:
        lines.append("")
        for issue in issues:
            lines.append(f"- [{issue.level.upper()}] `{issue.code}` ({issue.shot_id}) {issue.message}")

    lines.extend(["", "## Shot Execution Board", ""])
    for shot in view.get("shots", []):
        lines.append(f"### {shot['shot_id']} | {shot['time_range']}")
        lines.append(f"- Purpose: {shot['narrative_purpose']}")
        lines.append(f"- Scene/Action: {shot['scene']} / {shot['action']}")
        lines.append(f"- Mode / Transition: `{shot['control_mode']}` / `{shot['transition_to_next']}`")
        lines.append(f"- Why this mode: {shot['mode_reason']}")
        lines.append(f"- Risks: {', '.join(shot['risk_flags']) if shot['risk_flags'] else 'none'}")
        lines.append(f"- Execution: **{shot['execution_hint']['run_mode']}** — {shot['execution_hint']['note']}")
        lines.append(f"- Missing assets: {', '.join(shot['missing_assets']) if shot['missing_assets'] else 'none'}")
        lines.append(f"- Prompt: {shot['prompt_cn']}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _risk_badges(risks: List[str]) -> str:
    if not risks:
        return '<span class="badge ok">none</span>'
    return " ".join(f'<span class="badge warn">{html.escape(risk)}</span>' for risk in risks)


def render_panel_html(timeline: Dict[str, Any], view: Dict[str, Any], issues: List[ValidationIssue]) -> str:
    project = timeline.get("project", {})
    error_count = len([i for i in issues if i.level == "error"])
    warning_count = len([i for i in issues if i.level == "warning"])

    cards: List[str] = []
    for shot in view.get("shots", []):
        missing = ", ".join(shot["missing_assets"]) if shot["missing_assets"] else "none"
        cards.append(
            f"""
        <section class=\"card\" data-run-mode=\"{html.escape(shot['execution_hint']['run_mode'])}\">\n"
            f"<div class=\"card-head\"><h3>{html.escape(shot['shot_id'])}</h3><span class=\"time\">{html.escape(shot['time_range'])}</span></div>"
            f"<p><strong>Purpose:</strong> {html.escape(str(shot['narrative_purpose']))}</p>"
            f"<p><strong>Scene:</strong> {html.escape(str(shot['scene']))}</p>"
            f"<p><strong>Action:</strong> {html.escape(str(shot['action']))}</p>"
            f"<p><strong>Mode / Transition:</strong> <code>{html.escape(str(shot['control_mode']))}</code> / <code>{html.escape(str(shot['transition_to_next']))}</code></p>"
            f"<p><strong>Why:</strong> {html.escape(str(shot['mode_reason']))}</p>"
            f"<p><strong>Execution:</strong> <span class=\"run-mode\">{html.escape(shot['execution_hint']['run_mode'])}</span> — {html.escape(shot['execution_hint']['note'])}</p>"
            f"<p><strong>Risks:</strong> {_risk_badges(shot['risk_flags'])}</p>"
            f"<p><strong>Missing Assets:</strong> {html.escape(missing)}</p>"
            f"<details><summary>Prompt Details</summary><p><strong>Prompt:</strong> {html.escape(shot['prompt_cn'])}</p><p><strong>Negative:</strong> {html.escape(shot['negative_prompt'])}</p></details>"
          "</section>"
            """
        )

    issue_items = "".join(
        f"<li><strong>[{html.escape(i.level.upper())}] {html.escape(i.code)}</strong> ({html.escape(i.shot_id)}) {html.escape(i.message)}</li>"
        for i in issues
    ) or "<li>No issues</li>"

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Timeline Panel - {html.escape(project.get('title', 'Untitled'))}</title>
  <style>
    :root {{ --bg:#0b1020; --fg:#e8ecff; --card:#151b33; --muted:#9fb0e0; --line:#2a355f; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; background:var(--bg); color:var(--fg); }}
    .wrap {{ max-width:1100px; margin:0 auto; padding:24px; }}
    .meta,.issues,.card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; }}
    .meta,.issues {{ padding:14px; margin-bottom:14px; }}
    .toolbar {{ display:flex; gap:8px; margin:12px 0 18px; }}
    button {{ border:1px solid var(--line); background:#1b2447; color:var(--fg); border-radius:8px; padding:8px 12px; cursor:pointer; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:12px; }}
    .card {{ padding:14px; }}
    .card-head {{ display:flex; justify-content:space-between; align-items:center; gap:12px; }}
    .time {{ color:var(--muted); font-size:12px; }}
    .badge {{ display:inline-block; margin-right:6px; margin-top:4px; padding:2px 8px; border-radius:999px; font-size:12px; }}
    .badge.ok {{ background:rgba(46,204,113,.18); color:#9ff0bf; border:1px solid rgba(46,204,113,.35); }}
    .badge.warn {{ background:rgba(243,156,18,.18); color:#ffd39b; border:1px solid rgba(243,156,18,.35); }}
    code {{ background:#1a2449; border:1px solid var(--line); padding:1px 6px; border-radius:6px; }}
  </style>
</head>
<body>
  <main class=\"wrap\">
    <h1>Timeline Creator Panel</h1>
    <section class=\"meta\">
      <p><strong>Project:</strong> {html.escape(project.get('title', 'Untitled'))}</p>
      <p><strong>Idea:</strong> {html.escape(project.get('idea', ''))}</p>
      <p><strong>Target Duration:</strong> {html.escape(str(project.get('target_duration_sec', '?')))}s</p>
      <p><strong>Generated At:</strong> {html.escape(view['meta']['generated_at'])}</p>
      <p><strong>Validation:</strong> errors={error_count}, warnings={warning_count}</p>
    </section>

    <div class=\"toolbar\">
      <button onclick=\"filterMode('all')\">All</button>
      <button onclick=\"filterMode('parallelizable')\">Parallelizable</button>
      <button onclick=\"filterMode('sequential')\">Sequential</button>
    </div>

    <section class=\"grid\" id=\"grid\">{''.join(cards)}</section>

    <section class=\"issues\">
      <h2>Validation Issues</h2>
      <ul>{issue_items}</ul>
    </section>
  </main>
  <script>
    function filterMode(mode) {{
      const cards = document.querySelectorAll('.card');
      cards.forEach(c => {{ c.style.display = (mode === 'all' || c.dataset.runMode === mode) ? 'block' : 'none'; }});
    }}
  </script>
</body>
</html>
"""


def render_asset_checklist(asset_idx: Dict[str, Dict[str, Any]], view: Dict[str, Any]) -> str:
    lines: List[str] = ["# Asset Checklist", "", f"- Total registered assets: **{len(asset_idx)}**", "", "## Registered Assets"]
    for aid, asset in sorted(asset_idx.items(), key=lambda x: x[0]):
        lines.append(f"- `{aid}` | {asset.get('type')} | `{asset.get('path')}`")

    lines.append("")
    lines.append("## Missing by Shot")
    missing = [(shot["shot_id"], m) for shot in view.get("shots", []) for m in shot.get("missing_assets", [])]
    if not missing:
        lines.append("- none")
    else:
        for sid, mid in missing:
            lines.append(f"- {sid}: `{mid}`")

    return "\n".join(lines).strip() + "\n"


def render_shot_prompt_pack(timeline: Dict[str, Any]) -> str:
    lines: List[str] = ["# Shot Prompt Pack", ""]
    for shot in timeline.get("shots", []):
        lines.append(f"## {shot.get('shot_id')}")
        lines.append(f"- mode: `{shot.get('control_mode')}`")
        lines.append(f"- transition: `{shot.get('transition_to_next')}`")
        lines.append(f"- prompt_cn: {shot.get('prompt_cn', '')}")
        lines.append(f"- negative_prompt: {shot.get('negative_prompt', '')}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build timeline execution panel and execution pack")
    parser.add_argument("--timeline", required=True, help="Path to timeline.v1.json")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    args = parser.parse_args()

    timeline_path = Path(args.timeline).resolve()
    out_dir = Path(args.out_dir).resolve()

    timeline = read_json(timeline_path)
    issues = validate_timeline(timeline)
    has_errors = any(i.level == "error" for i in issues)

    asset_idx = index_assets(timeline)
    view = build_timeline_view(timeline, asset_idx)

    write_json(out_dir / "timeline.v1.json", timeline)
    write_json(out_dir / "timeline.view.v1.json", view)
    write_json(
        out_dir / "validation.report.json",
        {
            "generated_at": now_iso(),
            "error_count": len([i for i in issues if i.level == "error"]),
            "warning_count": len([i for i in issues if i.level == "warning"]),
            "issues": [i.__dict__ for i in issues],
            "valid": not has_errors,
        },
    )

    panel_md = render_panel_markdown(timeline, view, issues)
    panel_html = render_panel_html(timeline, view, issues)
    write_text(out_dir / "panel.md", panel_md)
    write_text(out_dir / "panel.html", panel_html)
    write_text(out_dir / "index.html", panel_html)
    write_text(out_dir / "asset-checklist.md", render_asset_checklist(asset_idx, view))
    write_text(out_dir / "shot-prompt-pack.md", render_shot_prompt_pack(timeline))

    print(f"Panel generated at: {out_dir}")
    print(f"Open this file in browser: {out_dir / 'index.html'}")
    if has_errors:
        print("Validation errors detected. See validation.report.json")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
