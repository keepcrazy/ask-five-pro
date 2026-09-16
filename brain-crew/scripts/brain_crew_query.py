#!/usr/bin/env python3
"""Thin Query API adapter around the shared Ask Five Pro matcher."""

from __future__ import annotations

import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from matching_core import (
    RegistryError,
    load_registry_file,
    match_experts,
    recommendation_reason,
)


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
DEV_REGISTRY_PATH = PROJECT_DIR / "expert-registry.json"
_content_cache: dict[str, str] = {}


def find_registry_path(custom_path: Optional[str | os.PathLike[str]] = None) -> str:
    """Resolve the built-in registry or a caller-provided existing file.

    A caller-provided missing path is an error. In particular, the deleted
    references/expert-registry.json path is never redirected.
    """
    if custom_path is not None:
        path = Path(custom_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Registry not found: {path}")
        return str(path.resolve())
    if DEV_REGISTRY_PATH.is_file():
        return str(DEV_REGISTRY_PATH.resolve())
    raise FileNotFoundError(
        f"Built-in expert registry is missing: {DEV_REGISTRY_PATH}"
    )


@lru_cache(maxsize=8)
def load_registry(
    registry_path: Optional[str | os.PathLike[str]] = None,
) -> dict[str, Any]:
    path = find_registry_path(registry_path)
    try:
        data = load_registry_file(path)
    except RegistryError as exc:
        raise ValueError(str(exc)) from exc
    data["_registry_path"] = path
    return data


def resolve_expert_path(expert: dict[str, Any], registry_dir: str) -> str:
    path = Path(expert.get("path", ""))
    if path.is_absolute():
        return str(path)
    return str((Path(registry_dir) / path).resolve())


def query_experts(
    categories: list[str],
    tags: list[str],
    styles: Optional[list[str]] = None,
    mode: str = "consensus",
    limit: int = 5,
    exclude: Optional[list[str]] = None,
    metadata_only: bool = True,
    registry_path: Optional[str | os.PathLike[str]] = None,
    include: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Return matching experts while preserving the v2.2.3 function entrypoint.

    `styles` remains accepted for API compatibility. The shared mainline
    matcher owns mode style weighting; caller style hints do not create a
    second scoring formula.
    """
    del styles
    registry = load_registry(registry_path)
    topic = " ".join(tags)
    _, selected, _ = match_experts(
        registry["experts"],
        categories,
        topic,
        mode,
        panel_size=limit,
        include_ids=include or (),
        exclude_ids=exclude or (),
    )
    results = []
    for expert in selected:
        item = {
            "id": expert["id"],
            "name": expert["name"],
            "pack": expert["pack"],
            "core_domain": expert["core_domain"],
            "style": expert["style"],
            "topic_tags": expert["topic_tags"],
            "sensitivity": expert["sensitivity"],
            "score": expert["raw_score"],
            "reason": recommendation_reason(expert, categories, tags),
        }
        if not metadata_only:
            item["content"] = load_expert_content(
                expert["id"], registry_path=registry_path
            )
        results.append(item)
    return results


def query_panels(
    sub_topics: list[dict[str, Any]],
    mode: str = "consensus",
    max_per_panel: int = 5,
    ensure_diversity: bool = True,
    registry_path: Optional[str | os.PathLike[str]] = None,
) -> list[dict[str, Any]]:
    """Batch multiple matching requests; `turbo` is only a batch marker."""
    used_expert_ids: set[str] | None = set() if ensure_diversity else None
    panels = []
    for topic in sub_topics:
        exclude = list(used_expert_ids) if used_expert_ids is not None else None
        experts = query_experts(
            categories=topic.get("categories", []),
            tags=topic.get("tags", []),
            styles=topic.get("required_styles", []),
            mode=mode,
            limit=max_per_panel,
            exclude=exclude,
            metadata_only=True,
            registry_path=registry_path,
        )
        if used_expert_ids is not None:
            used_expert_ids.update(expert["id"] for expert in experts)
        panels.append(
            {
                "sub_topic_id": topic.get("id", f"topic-{len(panels)}"),
                "title": topic.get("title", ""),
                "experts": experts,
            }
        )
    return panels


def load_expert_content(
    expert_id: str,
    registry_path: Optional[str | os.PathLike[str]] = None,
    use_cache: bool = True,
) -> str:
    path = find_registry_path(registry_path)
    cache_key = f"{path}:{expert_id}"
    if use_cache and cache_key in _content_cache:
        return _content_cache[cache_key]

    registry = load_registry(registry_path)
    expert = next(
        (item for item in registry["experts"] if item.get("id") == expert_id),
        None,
    )
    content = ""
    if expert is not None:
        resolved = resolve_expert_path(expert, str(Path(path).parent))
        try:
            content = Path(resolved).read_text(encoding="utf-8")
        except OSError:
            content = ""
    if use_cache:
        _content_cache[cache_key] = content
    return content


def clear_content_cache() -> None:
    _content_cache.clear()


def _generate_reason(
    expert: dict[str, Any],
    categories: list[str],
    tags: list[str],
) -> str:
    """Backward-compatible helper retained for callers importing it."""
    return recommendation_reason(expert, categories, tags)


def get_registry_stats(
    registry_path: Optional[str | os.PathLike[str]] = None,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    packs: dict[str, int] = {}
    for expert in registry["experts"]:
        pack = expert.get("pack", "unknown")
        packs[pack] = packs.get(pack, 0) + 1
    return {
        "total_experts": len(registry["experts"]),
        "packs": packs,
        "registry_path": registry["_registry_path"],
        "schema_version": registry.get("schema_version", "unknown"),
    }


if __name__ == "__main__":
    print("=" * 70)
    print("Brain Crew Query Module Self-Test")
    print("=" * 70)
    stats = get_registry_stats()
    print(f"\nRegistry: {stats['registry_path']}")
    print(f"Total experts: {stats['total_experts']}")
    print(f"Packs: {stats['packs']}")

    start = time.time()
    result = query_experts(
        categories=["产品", "战略"],
        tags=["用户体验", "聚焦"],
        mode="consensus",
        limit=3,
    )
    print(f"Time: {(time.time() - start) * 1000:.2f}ms")
    for expert in result:
        print(
            f"  - {expert['name']} "
            f"(score={expert['score']}, reason={expert['reason']})"
        )
