#!/usr/bin/env python3
"""Validate the 40 bundled expert assets against their immutable source snapshot."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


BRAIN_CREW_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BRAIN_CREW_DIR.parent
DEFAULT_REGISTRY = BRAIN_CREW_DIR / "expert-registry.json"
DEFAULT_SOURCE_MAP = PROJECT_DIR / "tests" / "fixtures" / "baseline" / "expert-source-map.json"
EXPECTED_PACKS = {
    "core": 6,
    "brand": 10,
    "tech": 7,
    "enterprise": 12,
    "meta": 5,
}


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    try:
        block = text.split("---", 2)[1]
    except IndexError:
        return {}
    values = {}
    for line in block.splitlines():
        if not line or line[0].isspace() or line.startswith("-") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def git_bytes(revision: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{revision}:{path}"],
        cwd=PROJECT_DIR,
    )


def source_files(revision: str, directory: str) -> list[str]:
    output = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", revision, "--", directory],
        cwd=PROJECT_DIR,
        text=True,
    )
    return [line for line in output.splitlines() if line]


def flash_ids(path: Path) -> list[str]:
    pattern = re.compile(r"^### .+（([^）]+)）$", re.MULTILINE)
    return pattern.findall(path.read_text(encoding="utf-8"))


def validate(
    registry_path: Path,
    source_map_path: Path,
    *,
    compare_source: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "errors": [f"invalid registry: {exc}"], "warnings": []}
    source_map: dict[str, Any] = {"experts": []}
    if compare_source:
        try:
            source_map = json.loads(source_map_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return {"ok": False, "errors": [f"invalid source map: {exc}"], "warnings": []}

    experts = registry.get("experts", [])
    ids = [expert.get("id") for expert in experts]
    if len(experts) != 40:
        errors.append(f"expected 40 experts, found {len(experts)}")
    if len(ids) != len(set(ids)):
        errors.append("registry contains duplicate ids")
    if any(not expert_id for expert_id in ids):
        errors.append("registry contains an empty id")

    pack_counts = {pack: 0 for pack in EXPECTED_PACKS}
    for expert in experts:
        pack = expert.get("pack")
        pack_counts[pack] = pack_counts.get(pack, 0) + 1
    if pack_counts != EXPECTED_PACKS:
        errors.append(f"pack distribution mismatch: {pack_counts}")

    mapping = {item["id"]: item for item in source_map.get("experts", [])}
    if compare_source and set(mapping) != set(ids):
        errors.append("source map ids do not exactly match registry ids")

    checked_source_files = 0
    for expert in experts:
        expert_id = expert["id"]
        relative = Path(expert.get("path", ""))
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"{expert_id}: path is not package-relative: {relative}")
            continue
        target = (registry_path.parent / relative).resolve()
        try:
            target.relative_to(registry_path.parent.resolve())
        except ValueError:
            errors.append(f"{expert_id}: path escapes Brain Crew: {target}")
            continue
        if not target.is_file():
            errors.append(f"{expert_id}: missing SKILL.md: {target}")
            continue

        frontmatter = parse_frontmatter(target)
        if frontmatter.get("id") != expert_id:
            errors.append(
                f"{expert_id}: frontmatter id is {frontmatter.get('id')!r}"
            )
        if frontmatter.get("name") != target.parent.name:
            errors.append(
                f"{expert_id}: frontmatter name {frontmatter.get('name')!r} "
                f"does not match directory {target.parent.name!r}"
            )

        source = mapping.get(expert_id) if compare_source else None
        if not source:
            continue
        revision = source["revision"]
        source_path = source["source_path"]
        source_dir = str(Path(source_path).parent)
        try:
            shipped_files = source_files(revision, source_dir)
        except subprocess.CalledProcessError as exc:
            errors.append(f"{expert_id}: cannot inspect fixed source: {exc}")
            continue
        if not shipped_files:
            errors.append(f"{expert_id}: fixed source directory is empty")
            continue
        for shipped in shipped_files:
            suffix = Path(shipped).relative_to(source_dir)
            current = target.parent / suffix
            if not current.is_file():
                errors.append(f"{expert_id}: missing source asset {suffix}")
                continue
            try:
                expected = git_bytes(revision, shipped)
            except subprocess.CalledProcessError as exc:
                errors.append(f"{expert_id}: cannot read source asset {shipped}: {exc}")
                continue
            checked_source_files += 1
            if current.read_bytes() != expected:
                errors.append(f"{expert_id}: source asset differs: {suffix}")

    profile_dir = registry_path.parent / "flash-profiles"
    profile_ids: list[str] = []
    if not profile_dir.is_dir():
        errors.append(f"Flash profile directory not found: {profile_dir}")
    else:
        for profile_path in sorted(profile_dir.rglob("*.md")):
            if profile_path.parent != profile_dir:
                errors.append(f"nested Flash profile is not allowed: {profile_path}")
            try:
                ids_in_file = flash_ids(profile_path)
            except OSError as exc:
                errors.append(f"cannot read Flash profile {profile_path}: {exc}")
                continue
            if len(ids_in_file) != 1:
                errors.append(
                    f"Flash profile must contain exactly one expert id: {profile_path}"
                )
                continue
            profile_id = ids_in_file[0]
            profile_ids.append(profile_id)
            if profile_path.stem != profile_id:
                errors.append(
                    f"Flash profile filename/id mismatch: "
                    f"{profile_path.name} contains {profile_id}"
                )
    missing_profiles = sorted(set(ids) - set(profile_ids))
    orphan_profiles = sorted(set(profile_ids) - set(ids))
    duplicate_profiles = sorted(
        {expert_id for expert_id in profile_ids if profile_ids.count(expert_id) > 1}
    )
    if missing_profiles:
        errors.append(f"missing Flash profiles: {missing_profiles}")
    if orphan_profiles:
        errors.append(f"orphan Flash profiles: {orphan_profiles}")
    if duplicate_profiles:
        errors.append(f"duplicate Flash profiles: {duplicate_profiles}")

    return {
        "ok": not errors,
        "experts_checked": len(experts),
        "source_files_checked": checked_source_files,
        "pack_counts": pack_counts,
        "flash_profiles_checked": len(profile_ids),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--source-map", type=Path, default=DEFAULT_SOURCE_MAP)
    parser.add_argument(
        "--installed-only",
        action="store_true",
        help="check packaged files and mappings without comparing the Git source snapshot",
    )
    args = parser.parse_args()
    result = validate(
        args.registry.resolve(),
        args.source_map.resolve(),
        compare_source=not args.installed_only,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
