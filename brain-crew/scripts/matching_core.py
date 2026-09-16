#!/usr/bin/env python3
"""Shared expert matching logic for Ask Five Pro.

This module contains only the matching work that was already programmatic in
v2.2.3. It deliberately does not own roster confirmation, persona loading,
meeting orchestration, or synthesis.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable


CATEGORY_KEYWORDS = {
    "战略": ["战略", "方向", "定位", "愿景", "进入", "扩张"],
    "产品": ["产品", "功能", "需求", "用户", "体验", "MVP", "路线图"],
    "设计": ["设计", "UI", "交互", "视觉"],
    "技术": ["技术", "架构", "重构", "系统", "代码", "工程", "技术债"],
    "成本": ["成本", "预算", "费用", "投入", "ROI", "收益", "现金流"],
    "团队": ["团队", "组织", "人才", "招聘", "管理", "人员"],
    "内容": ["内容", "短视频", "视频", "创作", "选题", "爆款", "脚本"],
    "传播": ["传播", "品牌", "营销", "市场", "宣传", "推广", "公关", "短视频"],
    "增长": ["增长", "拉新", "留存", "转化", "漏斗", "获客", "矩阵"],
    "风险": ["风险", "失败", "合规", "法律", "安全", "危机"],
    "投资": ["投资", "融资", "估值", "股权", "回报"],
    "个人成长": ["职业", "成长", "学习", "选择", "人生"],
}

MODE_STYLE_PREFERENCES = {
    "consensus": ["全局观", "长期主义", "系统思维"],
    "debate": ["激进", "保守", "乐观", "悲观"],
    "red-team": ["批判", "逆向", "风险", "怀疑", "skeptical"],
    "jury": ["独立", "理性", "数据驱动"],
    "pre-mortem": ["风险", "逆向", "失败导向"],
    "tempering": ["批判", "验证", "严格", "系统思维", "怀疑"],
}

MODE_EXTRA_CATEGORIES = {
    "red-team": ["风险"],
    "pre-mortem": ["风险"],
    "tempering": ["风险", "验证"],
}

MODE_EXTRA_TAGS = {
    "red-team": [
        "风险控制", "逆向思考", "概念验证", "反货物崇拜", "黑天鹅",
        "反脆弱", "杠铃策略", "尾部风险", "不确定性", "认知偏误",
    ],
    "pre-mortem": [
        "风险控制", "逆向思考", "概念验证", "反货物崇拜", "黑天鹅",
        "反脆弱", "杠铃策略", "尾部风险", "不确定性", "认知偏误",
    ],
    "tempering": [
        "风险控制", "逆向思考", "概念验证", "反货物崇拜", "黑天鹅",
        "反脆弱", "杠铃策略", "尾部风险", "不确定性", "认知偏误",
        "系统思维", "验证",
    ],
}

# Only the three aliases approved by the refactor decision table.
CATEGORY_CANONICAL = {
    "团队": "团队",
    "组织": "团队",
    "技术": "技术",
    "工程": "技术",
    "风险": "风险",
    "风控": "风险",
}

MEETING_MODES = {
    "consensus",
    "debate",
    "red-team",
    "jury",
    "pre-mortem",
    "tempering",
}


class RegistryError(ValueError):
    """The installed expert registry is missing, empty, or invalid."""


def canonical_category(value: str) -> str:
    return CATEGORY_CANONICAL.get(value, value)


def canonical_categories(values: Iterable[str]) -> set[str]:
    return {canonical_category(value) for value in values if value}


def normalize_mode(mode: str) -> str:
    # turbo is a Query API batching marker, not a meeting mode.
    return "consensus" if mode == "turbo" else mode


def infer_categories(topic: str, mode: str | None = None) -> list[str]:
    """Infer categories using the v2.2.3 mainline keyword table."""
    found: set[str] = set()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in topic:
                found.add(category)
                break
    normalized_mode = normalize_mode(mode or "consensus")
    if normalized_mode in MODE_EXTRA_CATEGORIES:
        found.update(MODE_EXTRA_CATEGORIES[normalized_mode])
    return list(found)


def overlap_ratio(a: Iterable[str], b: Iterable[str]) -> float:
    set_a = set(a)
    set_b = set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / min(len(set_a), len(set_b))


def load_registry_file(path: str | Path) -> dict[str, Any]:
    registry_path = Path(path)
    if not registry_path.is_file():
        raise RegistryError(f"Registry not found: {registry_path}")
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Invalid registry: {registry_path}: {exc}") from exc
    experts = data.get("experts")
    if not isinstance(experts, list) or not experts:
        raise RegistryError(f"Registry contains no experts: {registry_path}")
    ids = [expert.get("id") for expert in experts]
    if any(not expert_id for expert_id in ids) or len(ids) != len(set(ids)):
        raise RegistryError(f"Registry contains missing or duplicate expert ids: {registry_path}")
    return data


def compute_scores(
    experts: list[dict[str, Any]],
    categories: list[str],
    topic: str,
    mode: str,
    *,
    include_ids: Iterable[str] = (),
    exclude_ids: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Score experts using the v2.2.3 mainline formula."""
    normalized_mode = normalize_mode(mode)
    preferred_styles = MODE_STYLE_PREFERENCES.get(
        normalized_mode, MODE_STYLE_PREFERENCES["consensus"]
    )
    category_set = canonical_categories(categories)
    include_set = set(include_ids)
    exclude_set = set(exclude_ids)
    # Retained for compatibility with the original tokenizer side effect.
    re.findall(r"[\u4e00-\u9fa5]{2,8}", topic)

    scores = []
    for expert in experts:
        expert_id = expert.get("id")
        if expert_id in exclude_set:
            continue
        if (
            expert.get("sensitivity") == "sensitive"
            and normalized_mode != "debate"
            and expert_id not in include_set
        ):
            continue

        core_domain = expert.get("core_domain", [])
        topic_tags = expert.get("topic_tags", [])
        style = expert.get("style", [])
        domain_score = overlap_ratio(
            canonical_categories(core_domain),
            category_set,
        )
        tag_matches = sum(1 for tag in topic_tags if tag in topic)
        tag_score = tag_matches / max(len(topic_tags), 1)
        style_matches = len(set(style) & set(preferred_styles))
        style_score = style_matches / max(len(preferred_styles), 1)

        mode_tag_bonus = 0.0
        if normalized_mode in MODE_EXTRA_TAGS:
            matched_mode_tags = set(topic_tags) & set(MODE_EXTRA_TAGS[normalized_mode])
            mode_tag_bonus = len(matched_mode_tags) * 0.5

        score = domain_score * 3 + tag_score * 2 + style_score + mode_tag_bonus
        scores.append(
            {
                "id": expert_id,
                "name": expert.get("name"),
                "pack": expert.get("pack"),
                "domain_score": round(domain_score, 2),
                "tag_score": round(tag_score, 2),
                "style_score": round(style_score, 2),
                "mode_tag_bonus": round(mode_tag_bonus, 2),
                "raw_score": round(score, 2),
                "core_domain": core_domain,
                "style": style,
                "topic_tags": topic_tags,
                "sensitivity": expert.get("sensitivity"),
                "path": expert.get("path"),
            }
        )
    return sorted(scores, key=lambda item: item["raw_score"], reverse=True)


def select_panel(
    scored_experts: list[dict[str, Any]],
    target_size: int,
) -> list[dict[str, Any]]:
    """Select a diverse panel and stop rather than filling with non-positive scores."""
    selected: list[dict[str, Any]] = []
    remaining = [dict(item) for item in scored_experts]
    while len(selected) < target_size and remaining:
        for candidate in remaining:
            penalty = 0.0
            for chosen in selected:
                if overlap_ratio(
                    canonical_categories(candidate["core_domain"]),
                    canonical_categories(chosen["core_domain"]),
                ) > 0.5:
                    penalty += 0.2
            candidate["adjusted_score"] = round(candidate["raw_score"] - penalty, 2)
        remaining.sort(key=lambda item: item["adjusted_score"], reverse=True)
        best = remaining[0]
        if best["adjusted_score"] <= 0:
            break
        selected.append(remaining.pop(0))
    return selected


def target_panel_size(category_count: int) -> int:
    return {1: 3, 2: 4}.get(category_count, 5)


def match_experts(
    experts: list[dict[str, Any]],
    categories: list[str],
    topic: str,
    mode: str,
    *,
    panel_size: int | None = None,
    include_ids: Iterable[str] = (),
    exclude_ids: Iterable[str] = (),
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    size = panel_size or target_panel_size(len(categories))
    scores = compute_scores(
        experts,
        categories,
        topic,
        mode,
        include_ids=include_ids,
        exclude_ids=exclude_ids,
    )
    return scores, select_panel(scores, size), size


def recommendation_reason(
    expert: dict[str, Any],
    categories: list[str],
    tags: list[str],
) -> str:
    domain_overlap = canonical_categories(expert.get("core_domain", [])) & canonical_categories(categories)
    tag_overlap = set(expert.get("topic_tags", [])) & set(tags)
    reasons = []
    if domain_overlap:
        reasons.append(f"覆盖{'/'.join(sorted(domain_overlap))}视角")
    if tag_overlap:
        reasons.append(f"命中{'/'.join(sorted(tag_overlap))}标签")
    return "，".join(reasons) if reasons else "风格匹配"
