#!/usr/bin/env python3
"""Ask Five Pro expert matching CLI.

The root Skill calls this entrypoint while the shared Brain Crew module owns
the matching rules.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SHARED_SCRIPTS = ROOT / "brain-crew" / "scripts"
sys.path.insert(0, str(SHARED_SCRIPTS))

from matching_core import (  # noqa: E402
    MEETING_MODES,
    RegistryError,
    infer_categories,
    load_registry_file,
    match_experts,
)


PUBLIC_SCORE_FIELDS = (
    "id",
    "name",
    "domain_score",
    "tag_score",
    "style_score",
    "mode_tag_bonus",
    "raw_score",
    "core_domain",
    "style",
)


def public_score(item: dict) -> dict:
    """只保留允许通过 CLI 对外返回的专家评分字段。"""
    return {key: item.get(key) for key in PUBLIC_SCORE_FIELDS}


def comma_list(value: str | None) -> list[str]:
    """把逗号分隔的命令行参数转换为已去除空白的非空字符串列表。"""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    """创建并配置专家匹配命令行参数解析器。"""
    parser = argparse.ArgumentParser(description="Ask Five Pro expert matching")
    parser.add_argument("--registry", required=True, help="Path to expert-registry.json")
    parser.add_argument("--topic", required=True, help="Topic text")
    parser.add_argument(
        "--mode",
        default="consensus",
        choices=sorted(MEETING_MODES),
    )
    parser.add_argument(
        "--categories",
        help="Comma-separated primary categories; inferred when omitted",
    )
    parser.add_argument("--panel-size", type=int, help="Override target panel size")
    parser.add_argument(
        "--include",
        help="Comma-separated explicitly named expert ids forced into the selected panel",
    )
    parser.add_argument(
        "--exclude",
        help="Comma-separated expert ids excluded by the user",
    )
    return parser


def main() -> int:
    """执行参数解析、专家匹配和 JSON 结果输出，并返回进程退出码。"""
    args = build_parser().parse_args()
    try:
        registry = load_registry_file(args.registry)
        categories = (
            comma_list(args.categories)
            if args.categories
            else infer_categories(args.topic, args.mode)
        )
        if not categories:
            raise ValueError("Cannot infer categories, please provide --categories")
        all_scores, selected, target_size = match_experts(
            registry["experts"],
            categories,
            args.topic,
            args.mode,
            panel_size=args.panel_size,
            include_ids=comma_list(args.include),
            exclude_ids=comma_list(args.exclude),
        )
    except (RegistryError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1

    result = {
        "topic": args.topic,
        "mode": args.mode,
        "primary_categories": categories,
        "target_panel_size": target_size,
        "all_scores": [public_score(item) for item in all_scores],
        "selected_panel": [public_score(item) for item in selected],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
