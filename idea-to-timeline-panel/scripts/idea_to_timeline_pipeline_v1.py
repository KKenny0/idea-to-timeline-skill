#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slugify(text: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "-" for ch in text.strip())
    while "--" in clean:
        clean = clean.replace("--", "-")
    return clean.strip("-")[:48] or "idea"


def default_assets() -> Dict[str, List[Dict[str, Any]]]:
    return {
        "images": [
            {"asset_id": "img_char_main_front", "type": "image", "path": "assets/characters/main/front.png", "usage_tags": ["main", "front"]},
            {"asset_id": "img_char_main_side", "type": "image", "path": "assets/characters/main/side.png", "usage_tags": ["main", "side"]},
            {"asset_id": "img_scene_primary", "type": "image", "path": "assets/scenes/primary.png", "usage_tags": ["scene", "primary"]},
        ],
        "videos": [],
        "audios": [
            {"asset_id": "aud_bgm_default", "type": "audio", "path": "assets/audio/bgm/default.mp3", "usage_tags": ["bgm"]}
        ],
    }


def build_timeline_from_idea(idea: str, title: str, project_id: str, duration_sec: int = 45) -> Dict[str, Any]:
    shot_boundaries = [(0, 8), (8, 16), (16, 24), (24, 34), (34, duration_sec)]
    purposes = ["铺垫", "冲突", "冲突", "反转", "收束"]
    modes = ["i2v", "multiref", "keyframes", "t2v", "i2v"]
    transitions = ["cut", "continuous", "continuous", "cut", "end"]
    scenes = ["外景入口", "主场景内部", "主场景内部", "高能反转点", "外景收束"]
    actions = [
        "主角进入事件现场并建立动机",
        "主角意识到局势并出现情绪冲突",
        "连续动作与反应推进冲突",
        "发生反转并拉高节奏",
        "结果落地并完成收束",
    ]

    shots: List[Dict[str, Any]] = []
    for idx, ((start, end), purpose, mode, transition, scene, action) in enumerate(
        zip(shot_boundaries, purposes, modes, transitions, scenes, actions), start=1
    ):
        sid = f"S{idx:02d}"
        duration = end - start
        shots.append(
            {
                "shot_id": sid,
                "start_sec": start,
                "end_sec": end,
                "duration_sec": duration,
                "narrative_purpose": purpose,
                "scene": scene,
                "subjects": ["char_main"],
                "action": action,
                "camera": {
                    "shot_size": "中景" if idx in {1, 4} else "中近景",
                    "angle": "平视",
                    "movement": "缓推" if transition == "cut" else "连续跟随",
                    "tempo": "慢" if idx in {1, 5} else "中",
                },
                "transition_to_next": transition,
                "control_mode": mode,
                "refs": {
                    "image_asset_ids": ["img_char_main_front", "img_scene_primary"] if mode == "multiref" else ["img_char_main_front"],
                    "video_asset_ids": [],
                    "audio_asset_ids": [],
                },
                "prompt_cn": f"基于idea: {idea}。镜头{sid}，场景{scene}，动作：{action}，风格保持轻喜剧节奏与角色一致性。",
                "negative_prompt": "无水印、无字幕、无畸形肢体、无面部漂移",
                "seedance_plan": {
                    "duration_sec": duration,
                    "aspect_ratio": "16:9",
                    "resolution_hint": "1080p",
                    "ref_binding": {
                        "images": ["@图片1", "@图片2"] if mode == "multiref" else ["@图片1"],
                        "videos": [],
                        "audios": [],
                    },
                    "timeline_prompt_segments": [
                        {"range": f"0-{max(1, duration // 2)}s", "text": f"{sid} 前半段推进"},
                        {"range": f"{max(1, duration // 2) + 1}-{duration}s", "text": f"{sid} 后半段收束"},
                    ],
                    "continuity_note": "与前后镜头保持角色服装和构图连续性",
                },
                "retry_policy": {"max_retries": 2, "fallback_mode": "i2v"},
            }
        )

    return {
        "meta": {
            "schema": "timeline.v1",
            "schema_version": "1.0.0",
            "created_at": now_iso(),
            "generated_by": "idea_to_timeline_pipeline_v1",
            "language": "zh-CN",
        },
        "project": {
            "project_id": project_id,
            "title": title,
            "idea": idea,
            "target_duration_sec": duration_sec,
            "aspect_ratio": "16:9",
            "fps": 24,
            "resolution": "1920x1080",
        },
        "global_style": {
            "genre": "都市轻喜剧",
            "tone": "轻快、反差",
            "visual_style": "国漫电影感",
            "palette": "暖色主调 + 对比色点缀",
            "negative_prompt_global": "无水印、无字幕、无人物闪烁",
        },
        "assets": default_assets(),
        "characters": [
            {
                "character_id": "char_main",
                "name": "主角",
                "profile": "有明显个性特征的叙事主角",
                "look": "主角基础服装与可识别轮廓",
                "refs": {"image_asset_ids": ["img_char_main_front", "img_char_main_side"]},
                "continuity_priority": 95,
            }
        ],
        "shots": shots,
        "audio_plan": {
            "tts_enabled": True,
            "bgm_asset_id": "aud_bgm_default",
            "sfx_strategy": "balanced",
            "dialogue_tracks": [],
        },
        "qa_policy": {
            "score_threshold": 75,
            "weights": {
                "narrative": 25,
                "consistency": 25,
                "motion_naturalness": 20,
                "style_unity": 15,
                "av_sync": 15,
            },
            "auto_regen": {"max_rounds": 2},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Idea -> Timeline HTML Panel pipeline")
    parser.add_argument("--idea", required=True, help="User idea text")
    parser.add_argument("--title", default="Idea Timeline Panel", help="Project title")
    parser.add_argument("--duration-sec", type=int, default=45, help="Target duration in seconds")
    parser.add_argument("--run-id", default=None, help="Run id under output root")
    parser.add_argument("--output-root", default="outputs/timeline-panel", help="Directory root for run outputs")
    args = parser.parse_args()

    run_id = args.run_id or f"idea-{slugify(args.title)}"
    out_dir = (Path(args.output_root).resolve() / run_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    project_id = f"proj-{slugify(args.title)}"
    timeline = build_timeline_from_idea(args.idea, args.title, project_id, args.duration_sec)

    timeline_input_path = out_dir / "timeline.input.v1.json"
    write_json(timeline_input_path, timeline)

    panel_script = Path(__file__).resolve().parent / "timeline_panel_v1.py"
    cmd = [
        "python3",
        str(panel_script),
        "--timeline",
        str(timeline_input_path),
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
    print(f"Idea pipeline completed. Open: {out_dir / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
