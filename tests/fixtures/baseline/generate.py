#!/usr/bin/env python3
"""Generate immutable compatibility fixtures from the v2.2.3 Git baseline."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


BASELINE = "4627911"
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True)


def classify_path(path: str) -> str:
    if path.startswith("brain-crew/packs/"):
        return "expert_asset"
    if path.startswith("brain-crew/tests/") or path in {
        "decisions-log.md",
        "tests/brain-crew-integration-report.json",
        "tests/darwin-evaluation-baseline.md",
        "tests/darwin-evaluation-v2.md",
        "tests/darwin-evaluation-v3.md",
        "tests/full-test-outputs.md",
        "tests/validation-checklist-v2.0.5.md",
    }:
        return "historical_evidence"
    if path.startswith("tests/") or path == "test-prompts.json":
        return "test"
    if path.startswith("scripts/") or path.startswith("brain-crew/scripts/"):
        return "tooling"
    if path.endswith(".md"):
        return "documentation"
    return "runtime_asset"


def build_manifest() -> dict:
    entries = []
    raw = run("git", "ls-tree", "-r", BASELINE)
    for line in raw.splitlines():
        metadata, path = line.split("\t", 1)
        mode, obj_type, object_id = metadata.split()
        entries.append(
            {
                "path": path,
                "mode": mode,
                "type": obj_type,
                "object_id": object_id,
                "category": classify_path(path),
            }
        )
    return {"baseline": BASELINE, "file_count": len(entries), "files": entries}


def baseline_bytes(path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{BASELINE}:{path}"],
        cwd=ROOT,
    )


def run_json(command: list[str], *, cwd: Path = ROOT) -> dict:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return json.loads(completed.stdout)


def build_boundary_cases() -> dict:
    cases = [
        "我们要不要做短视频矩阵？",
        "我最近胸口疼，是不是心脏病？",
        "这份劳动合同有没有坑？",
        "买入特斯拉股票靠谱吗？",
        "今天最新股价是多少？",
        "我想到自杀，感觉很绝望",
        "这个合同涉及投资，今天必须决定",
    ]
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        script = tmp / "boundary-guard.py"
        script.write_bytes(baseline_bytes("scripts/boundary-guard.py"))
        return {
            "baseline": BASELINE,
            "cases": [
                {
                    "prompt": prompt,
                    "result": run_json([sys.executable, str(script), prompt], cwd=tmp),
                }
                for prompt in cases
            ],
        }


def build_matching_cases() -> dict:
    cases = [
        {
            "id": "one-category",
            "topic": "产品路线应该如何取舍？",
            "mode": "consensus",
            "categories": "产品",
        },
        {
            "id": "two-categories",
            "topic": "短视频矩阵怎样获得增长？",
            "mode": "consensus",
            "categories": "内容,增长",
        },
        {
            "id": "three-categories",
            "topic": "是否裁撤团队并 all-in AI 客服？",
            "mode": "tempering",
            "categories": "战略,团队,风险",
        },
        {
            "id": "red-team",
            "topic": "我们要不要进入东南亚市场？",
            "mode": "red-team",
            "categories": "战略,风险",
        },
    ]
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        script = tmp / "match-experts.py"
        registry = tmp / "expert-registry.json"
        script.write_bytes(baseline_bytes("scripts/match-experts.py"))
        registry.write_bytes(baseline_bytes("references/expert-registry.json"))
        output = []
        for case in cases:
            command = [
                sys.executable,
                str(script),
                "--registry",
                str(registry),
                "--topic",
                case["topic"],
                "--mode",
                case["mode"],
                "--categories",
                case["categories"],
            ]
            output.append({**case, "result": run_json(command, cwd=tmp)})
        return {"baseline": BASELINE, "cases": output}


def build_query_cases() -> dict:
    cases = [
        {
            "id": "consensus",
            "categories": ["内容", "增长"],
            "tags": ["短视频", "矩阵"],
            "mode": "consensus",
        },
        {
            "id": "debate-sensitive",
            "categories": ["谈判", "权力"],
            "tags": ["舆论操控"],
            "mode": "debate",
        },
    ]
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        module_path = tmp / "brain_crew_query.py"
        registry = tmp / "expert-registry.json"
        module_path.write_bytes(
            baseline_bytes("brain-crew/scripts/brain_crew_query.py")
        )
        registry.write_bytes(baseline_bytes("brain-crew/expert-registry.json"))
        driver = r'''
import importlib.util
import json
import sys

module_path, registry_path, raw_cases = sys.argv[1:]
spec = importlib.util.spec_from_file_location("baseline_brain_crew_query", module_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)
output = []
for case in json.loads(raw_cases):
    result = module.query_experts(
        categories=case["categories"],
        tags=case["tags"],
        mode=case["mode"],
        limit=5,
        registry_path=registry_path,
    )
    output.append({
        **case,
        "result": [
            {"id": item["id"], "score": item["score"], "reason": item["reason"]}
            for item in result
        ],
    })
print(json.dumps({"baseline": "4627911", "cases": output}, ensure_ascii=False))
'''
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = "0"
        generated = subprocess.check_output(
            [
                sys.executable,
                "-c",
                driver,
                str(module_path),
                str(registry),
                json.dumps(cases, ensure_ascii=False),
            ],
            cwd=tmp,
            text=True,
            env=env,
        )
        return json.loads(generated)


def build_expert_source_map() -> dict:
    registry = json.loads(
        run("git", "show", f"{BASELINE}:brain-crew/expert-registry.json")
    )
    experts = []
    for expert in registry["experts"]:
        source_path = expert["path"].replace(
            "<runtime-skills-dir>/brain-crew/", "brain-crew/"
        )
        experts.append(
            {
                "id": expert["id"],
                "repository": "local-git:ask-five-pro",
                "revision": BASELINE,
                "source_path": source_path,
                "target_path": source_path,
            }
        )
    return {
        "source_note": (
            "This checkout has no configured Git remote. The immutable local Git "
            "commit is the verified source snapshot for all bundled experts."
        ),
        "experts": experts,
    }


def migration_for(path: str) -> dict:
    historical_root = {
        "decisions-log.md",
        "tests/brain-crew-integration-report.json",
        "tests/darwin-evaluation-baseline.md",
        "tests/darwin-evaluation-v2.md",
        "tests/darwin-evaluation-v3.md",
        "tests/empty-registry-test.md",
        "tests/full-test-outputs.md",
        "tests/mock-expert-test.md",
        "tests/validation-checklist-v2.0.5.md",
    }
    explicit = {
        "references/expert-registry.json": ("delete", None, "replaced by the single Brain Crew registry"),
        "references/expert-registry.json.bak": ("delete", None, "empty legacy backup is not a product asset"),
        "brain-crew/docs/ask-five-engine-integration-prompt.md": ("delete", None, "obsolete Engine-only integration material"),
        "references/parliament-mode-templates.md": ("rewrite", "references/mode-templates.md", "relocate and align six-mode templates with approved decisions 10 and 19-23"),
        "references/output-example.md": ("rewrite", "references/output-examples.md", "relocate and align the non-normative example with approved decisions 19-20"),
        "references/flash-profiles.md": ("move", "brain-crew/flash-profiles.md", "expert profiles belong with Brain Crew assets"),
        "references/EXPERT_SKILL_SPEC.md": ("rewrite", "brain-crew/docs/expert-skill-spec.md", "relocate and align the contract with approved decisions 1-5 and portable Registry paths"),
        "references/matching-algorithm.md": ("rewrite", "brain-crew/docs/matching-algorithm.md", "relocate and align matching documentation with approved decisions 6-14"),
        "references/artifact-templates.md": ("merge", "references/mode-templates.md", "mode material is consolidated"),
        "references/ask-five-cheatsheet.md": ("merge", "SKILL.md", "normative workflow remains discoverable from the root Skill"),
        "references/failure-modes.md": ("merge", "SKILL.md", "failure handling remains normative"),
        "references/darwin-roadmap.md": ("move", "tests/evidence/references/darwin-roadmap.md", "historical evaluation material"),
        "brain-crew/docs/overlap-matrix.md": ("move", "tests/evidence/brain-crew-docs/overlap-matrix.md", "historical overlap report"),
        "brain-crew/docs/pack-recommendation.md": ("move", "tests/evidence/brain-crew-docs/pack-recommendation.md", "historical pack recommendation"),
        "test-prompts.json": ("move", "tests/fixtures/workflow-prompts.json", "active fixtures live under tests"),
        "tests/mock-expert-registry.json": ("rewrite", "tests/fixtures/mock-expert-registry.json", "relocate the fixture and update its relative paths and approved Registry normalization"),
        "tests/mock-expert/SKILL.md": ("rewrite", "tests/fixtures/mock-expert/SKILL.md", "relocate the fixture and replace obsolete Engine-only wording"),
        "tests/mock-experts/mock-cmo/SKILL.md": ("rewrite", "tests/fixtures/mock-experts/mock-cmo/SKILL.md", "relocate the fixture and replace obsolete Engine-only wording"),
        "tests/mock-experts/mock-cto/SKILL.md": ("rewrite", "tests/fixtures/mock-experts/mock-cto/SKILL.md", "relocate the fixture and replace obsolete Engine-only wording"),
        "tests/mock-experts/mock-product-lead/SKILL.md": ("rewrite", "tests/fixtures/mock-experts/mock-product-lead/SKILL.md", "relocate the fixture and replace obsolete Engine-only wording"),
        "tests/mock-experts/mock-risk-officer/SKILL.md": ("rewrite", "tests/fixtures/mock-experts/mock-risk-officer/SKILL.md", "relocate the fixture and replace obsolete Engine-only wording"),
    }
    if path in explicit:
        action, target, reason = explicit[path]
    elif path.startswith("brain-crew/tests/"):
        action = "move"
        target = "tests/evidence/brain-crew/" + path.removeprefix("brain-crew/tests/")
        reason = "historical LLM output or report"
    elif path in {
        "brain-crew/scripts/auto-structure-enhance.py",
        "brain-crew/scripts/benchmark.py",
        "brain-crew/scripts/check-registry.sh",
        "brain-crew/scripts/compute-overlap-matrix.py",
        "brain-crew/scripts/darwin-quick-score.py",
        "brain-crew/scripts/diagnose-experts.py",
        "brain-crew/scripts/evaluate-llm-outputs.py",
        "brain-crew/scripts/final-polish-bottom10.py",
        "brain-crew/scripts/refine-actionability.py",
        "brain-crew/scripts/remove-expert-disclaimers.py",
        "brain-crew/scripts/run-critique-meeting.py",
        "brain-crew/scripts/run-real-prompt-tests.py",
        "brain-crew/scripts/test-engine-integration.py",
    }:
        action = "move"
        target = "tests/evidence/legacy-tools/" + Path(path).name
        reason = "legacy evaluation or mutation tool; not part of product runtime"
    elif path in historical_root:
        action = "move"
        target = "tests/evidence/" + Path(path).name
        reason = "historical result, not a current test"
    elif path in {
        "brain-crew/expert-registry.json",
        "SKILL.md",
        "README.md",
        "brain-crew/SKILL.md",
        "brain-crew/README.md",
        "brain-crew/CONTRIBUTING.md",
        "brain-crew/EXPERT_CRITERIA.md",
        "brain-crew/packs/extension/README.md",
        "references/anti-patterns.md",
        "references/expert-fallback-profiles.md",
        "scripts/boundary-guard.py",
        "scripts/check-experts.sh",
        "scripts/validate-expert.sh",
    }:
        action, target = "rewrite", path
        if path == "brain-crew/expert-registry.json":
            reason = "apply approved decisions 4-5 and portable package-relative paths"
        else:
            reason = "remove conflicts while preserving product behavior"
    elif path in {
        "scripts/match-experts.py",
        "brain-crew/scripts/brain_crew_query.py",
        "tests/brain-crew-integration-test.py",
        "tests/run-full-test.sh",
    }:
        action, target, reason = "rewrite", path, "consolidate duplicate logic or replace stale validation"
    else:
        action, target, reason = "keep", path, "preserved baseline asset"
    return {"source": path, "action": action, "target": target, "reason": reason}


def build_migration_map(manifest: dict) -> dict:
    entries = [migration_for(item["path"]) for item in manifest["files"]]
    return {
        "baseline": BASELINE,
        "source_file_count": len(entries),
        "entries": entries,
    }


def write_json(name: str, data: dict) -> None:
    (OUT / name).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    manifest = build_manifest()
    write_json("file-manifest.json", manifest)
    write_json("boundary-cases.json", build_boundary_cases())
    write_json("matching-cases.json", build_matching_cases())
    write_json("query-cases.json", build_query_cases())
    write_json("expert-source-map.json", build_expert_source_map())
    write_json("migration-map.json", build_migration_map(manifest))
    print("generated baseline fixtures in", OUT)


if __name__ == "__main__":
    main()
