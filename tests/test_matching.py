from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BRAIN = ROOT / "brain-crew"
REGISTRY = BRAIN / "expert-registry.json"
CLI = ROOT / "scripts" / "match-experts.py"
BASELINE = ROOT / "tests" / "fixtures" / "baseline" / "matching-cases.json"
sys.path.insert(0, str(BRAIN / "scripts"))
core = importlib.import_module("matching_core")
query = importlib.import_module("brain_crew_query")


def run_cli(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--registry",
            str(REGISTRY),
            *args,
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


class MatchingTests(unittest.TestCase):
    def test_unaffected_mainline_fixtures_remain_exact(self) -> None:
        fixture = json.loads(BASELINE.read_text(encoding="utf-8"))
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        sensitive_ids = {
            expert["id"]
            for expert in registry["experts"]
            if expert.get("sensitivity") == "sensitive"
        }
        for case in fixture["cases"]:
            if case["id"] not in {"one-category", "two-categories"}:
                continue
            result = json.loads(
                run_cli(
                    "--topic",
                    case["topic"],
                    "--mode",
                    case["mode"],
                    "--categories",
                    case["categories"],
                ).stdout
            )
            expected = case["result"]
            self.assertEqual(expected["target_panel_size"], result["target_panel_size"])
            # Decision 11 is an approved difference: sensitive experts are
            # removed before scoring outside debate or explicit naming.
            expected_scores = [
                item
                for item in expected["all_scores"]
                if item["id"] not in sensitive_ids
            ]
            self.assertEqual(expected_scores, result["all_scores"])
            self.assertEqual(expected["selected_panel"], result["selected_panel"])

    def test_cli_and_query_share_business_results(self) -> None:
        tags = ["短视频", "矩阵"]
        result = json.loads(
            run_cli(
                "--topic",
                " ".join(tags),
                "--mode",
                "consensus",
                "--categories",
                "内容,增长",
            ).stdout
        )
        queried = query.query_experts(
            ["内容", "增长"],
            tags,
            mode="consensus",
            limit=4,
            registry_path=REGISTRY,
        )
        self.assertEqual(
            [item["id"] for item in result["selected_panel"]],
            [item["id"] for item in queried],
        )
        self.assertEqual(
            [item["raw_score"] for item in result["selected_panel"]],
            [item["score"] for item in queried],
        )

    def test_only_three_bidirectional_aliases(self) -> None:
        pairs = [
            ("团队", "组织"),
            ("组织", "团队"),
            ("技术", "工程"),
            ("工程", "技术"),
            ("风险", "风控"),
            ("风控", "风险"),
        ]
        for category, domain in pairs:
            expert = {
                "id": f"{category}-{domain}",
                "name": "alias",
                "pack": "test",
                "core_domain": [domain],
                "topic_tags": [],
                "style": [],
                "sensitivity": "normal",
                "path": "unused",
            }
            score = core.compute_scores(
                [expert], [category], "", "consensus"
            )[0]["domain_score"]
            self.assertEqual(1.0, score, (category, domain))
        self.assertEqual("架构", core.canonical_category("架构"))
        self.assertEqual("人员", core.canonical_category("人员"))

    def test_sensitive_experts_require_name_or_debate(self) -> None:
        normal = query.query_experts(
            ["谈判", "权力"],
            ["谈判", "舆论"],
            mode="consensus",
            limit=5,
            registry_path=REGISTRY,
        )
        named = query.query_experts(
            ["谈判", "权力"],
            ["谈判", "舆论"],
            mode="consensus",
            limit=5,
            registry_path=REGISTRY,
            include=["donald-trump"],
        )
        debate = query.query_experts(
            ["谈判", "权力"],
            ["谈判", "舆论"],
            mode="debate",
            limit=5,
            registry_path=REGISTRY,
        )
        self.assertNotIn("donald-trump", {item["id"] for item in normal})
        self.assertIn("donald-trump", {item["id"] for item in named})
        self.assertIn("donald-trump", {item["id"] for item in debate})

    def test_panel_size_and_non_positive_stop(self) -> None:
        self.assertEqual(3, core.target_panel_size(1))
        self.assertEqual(4, core.target_panel_size(2))
        self.assertEqual(5, core.target_panel_size(3))
        selected = core.select_panel(
            [
                {"id": "zero", "raw_score": 0, "core_domain": []},
                {"id": "negative", "raw_score": -1, "core_domain": []},
            ],
            5,
        )
        self.assertEqual([], selected)

    def test_empty_and_corrupt_registries_are_installation_errors(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            for name, content in [
                ("empty.json", '{"experts": []}'),
                ("corrupt.json", "{"),
            ]:
                path = tmp / name
                path.write_text(content, encoding="utf-8")
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(CLI),
                        "--registry",
                        str(path),
                        "--topic",
                        "产品",
                        "--categories",
                        "产品",
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                self.assertNotEqual(0, completed.returncode)
                self.assertIn("error", json.loads(completed.stdout))

    def test_turbo_is_query_batching_not_a_meeting_mode(self) -> None:
        self.assertNotIn("turbo", core.MEETING_MODES)
        panels = query.query_panels(
            [
                {
                    "id": "one",
                    "title": "产品",
                    "categories": ["产品"],
                    "tags": ["用户体验"],
                }
            ],
            mode="turbo",
            max_per_panel=3,
            registry_path=REGISTRY,
        )
        self.assertEqual(1, len(panels))
        self.assertTrue(panels[0]["experts"])

    def test_query_adapter_contains_no_second_scoring_function(self) -> None:
        source = (BRAIN / "scripts" / "brain_crew_query.py").read_text(encoding="utf-8")
        self.assertNotIn("def _score_expert", source)
        self.assertNotIn("domain_score * 3", source)
        self.assertNotIn("input(", source)


if __name__ == "__main__":
    unittest.main()
