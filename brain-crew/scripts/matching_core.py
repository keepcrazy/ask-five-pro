#!/usr/bin/env python3
"""Shared expert matching logic for Ask Five Pro.

This module contains only the matching work that was already programmatic in
v2.2.3. It deliberately does not own roster confirmation, persona loading,
meeting orchestration, or synthesis.
"""

from __future__ import annotations

import json
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
    "consensus": [
        "全局观", "长期主义", "系统思维", "聚焦", "极简", "端到端控制",
        "延迟满足", "全局优化", "跨学科", "经典策略", "策略先行",
        "文化洞察", "整合传播", "信任资产", "社区运营", "哲学化",
        "极简表达", "教学型", "耐心拆解", "深邃", "Scaling", "简洁主义",
        "组合优先", "清晰高于聪明", "护城河", "客户痴迷", "利他主义",
        "敬天爱人", "实践哲学", "知行合一", "致良知", "本分", "平常心",
        "分布式", "自组织", "并行", "平台化", "软硬一体", "长期基础设施",
        "冷静", "压缩", "真诚", "克制", "直觉驱动",
    ],
    "debate": [
        "激进", "保守", "乐观", "悲观", "坦诚", "极端执行", "锋利",
        "讽刺", "直指本质", "市井智慧", "节奏控制", "现挂", "高频输出",
        "观点鲜明", "口语化", "干燥幽默", "对抗性", "交易思维", "戏剧化", "直白",
        "情绪共鸣", "追问", "反讽", "温和但锋利", "叙事化", "故事化",
    ],
    "red-team": [
        "批判", "逆向", "风险", "怀疑", "skeptical", "逆向思考", "反自欺",
        "成本拆解", "研究驱动", "洞察优先", "数据校准", "数据验收",
        "ROI纪律", "安全优先", "深度分析", "潜意识", "诊断式", "实事求是",
        "田野调查", "证据优先", "怀疑论", "杠铃策略", "反脆弱", "纪律性",
        "数据测算", "纪律定价", "风险前置", "QCD驱动", "追问", "问题优先",
        "复杂度克制",
    ],
    "jury": [
        "独立", "理性", "数据驱动", "成本拆解", "研究驱动", "洞察优先",
        "机制驱动", "数据校准", "实战拆解", "SOP驱动", "数据验收",
        "ROI纪律", "数据赛马", "纪律性", "实事求是", "田野调查", "证据优先",
        "实证", "评分驱动", "数据测算", "价值锚定", "纪律定价", "QCD驱动",
        "eval驱动", "问题优先", "实用主义", "留存优先",
    ],
    "pre-mortem": [
        "风险", "逆向", "失败导向", "逆向思考", "反自欺", "成本拆解",
        "数据验收", "ROI纪律", "安全优先", "深度分析", "诊断式", "怀疑论",
        "杠铃策略", "反脆弱", "纪律性", "风险前置", "小单快反", "形势优先",
        "问题优先", "复杂度克制",
    ],
    "tempering": [
        "批判", "验证", "严格", "系统思维", "怀疑", "聚焦",
        "从第一性原理出发", "第一性原理", "快速迭代", "留存优先",
        "研究驱动", "机制驱动", "数据校准", "实战拆解", "SOP驱动",
        "数据验收", "数据赛马", "耐心拆解", "组合优先", "清晰高于聪明",
        "实事求是", "证据优先", "实证", "迭代", "评分驱动", "实践哲学",
        "知行合一", "事上磨练", "QCD驱动", "小单快反", "软硬一体",
        "eval驱动", "问题优先", "复杂度克制", "实用主义", "节奏控制",
        "人物化", "蒸馏", "造人",
    ],
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

# 专业领域保留自身含义，同时补充用于匹配的标准父类别。
CATEGORY_PARENTS = {
    "AI": {"技术"},
    "AI产品": {"产品"},
    "Agent": {"技术"},
    "Skill": {"技术"},
    "学习": {"个人成长"},
    "品牌": {"传播"},
    "写作": {"内容"},
    "沟通": {"传播"},
    "私域运营": {"增长"},
    "直播电商": {"增长"},
    "调研": {"战略"},
    "谈判": {"战略"},
    "教育": {"个人成长"},
    "决策": {"战略"},
    "定价": {"成本"},
    "供应链": {"成本"},
    "认知谦逊": {"个人成长"},
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
    """把单个类别别名转换为统一类别，未配置的类别保持原值。"""
    return CATEGORY_CANONICAL.get(value, value)


def canonical_categories(values: Iterable[str]) -> set[str]:
    """批量归一化类别，补充标准父类别，并去除空值与重复项。"""
    categories: set[str] = set()
    for value in values:
        if not value:
            continue
        canonical = canonical_category(value)
        categories.add(canonical)
        categories.update(CATEGORY_PARENTS.get(canonical, set()))
    return categories


def infer_categories(topic: str, mode: str | None = None) -> list[str]:
    """根据议题关键词推断主类别，并补充当前会议模式要求的额外类别。"""
    found: set[str] = set()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in topic:
                found.add(category)
                break
    effective_mode = mode or "consensus"
    if effective_mode in MODE_EXTRA_CATEGORIES:
        found.update(MODE_EXTRA_CATEGORIES[effective_mode])
    return list(found)


def overlap_ratio(a: Iterable[str], b: Iterable[str]) -> float:
    """计算两个集合的重叠比例，分母取较小集合的元素数量。"""
    set_a = set(a)
    set_b = set(b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / min(len(set_a), len(set_b))


def load_registry_file(path: str | Path) -> dict[str, Any]:
    """读取专家 Registry，并校验文件、专家列表及专家 ID 的基本有效性。"""
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
    """过滤候选专家，计算领域、标签、风格及模式奖励分，并按总分降序排列。"""
    preferred_styles = MODE_STYLE_PREFERENCES.get(
        mode, MODE_STYLE_PREFERENCES["consensus"]
    )
    category_set = canonical_categories(categories)
    include_set = set(include_ids)
    exclude_set = set(exclude_ids)

    scores = []
    for expert in experts:
        expert_id = expert.get("id")
        if expert_id in exclude_set:
            continue
        if (
            expert.get("sensitivity") == "sensitive"
            and mode != "debate"
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
        style_score = style_matches / max(len(style), 1)

        mode_tag_bonus = 0.0
        if mode in MODE_EXTRA_TAGS:
            matched_mode_tags = set(topic_tags) & set(MODE_EXTRA_TAGS[mode])
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
    *,
    required_ids: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """先纳入用户点名专家，再按调整后得分补齐视角互补的名单。"""
    required_order = list(dict.fromkeys(required_ids))
    candidates_by_id = {item["id"]: dict(item) for item in scored_experts}
    selected = [candidates_by_id[expert_id] for expert_id in required_order]
    selected_ids = set(required_order)
    remaining = [
        dict(item) for item in scored_experts if item["id"] not in selected_ids
    ]
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
    """根据主类别数量确定默认专家人数：一个三人、两个四人、其余五人。"""
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
    """编排专家评分与名单选择，返回全部候选分数、入选名单和目标人数。"""
    required_ids = list(dict.fromkeys(include_ids))
    excluded_ids = set(exclude_ids)
    conflicts = sorted(set(required_ids) & excluded_ids)
    if conflicts:
        raise ValueError(f"Experts cannot be both included and excluded: {conflicts}")
    known_ids = {expert.get("id") for expert in experts}
    unknown_ids = sorted(set(required_ids) - known_ids)
    if unknown_ids:
        raise ValueError(f"Included experts not found in registry: {unknown_ids}")

    size = max(panel_size or target_panel_size(len(categories)), len(required_ids))
    scores = compute_scores(
        experts,
        categories,
        topic,
        mode,
        include_ids=required_ids,
        exclude_ids=excluded_ids,
    )
    return scores, select_panel(scores, size, required_ids=required_ids), size
