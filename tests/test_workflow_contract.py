from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
BRAIN_SKILL = (ROOT / "brain-crew" / "SKILL.md").read_text(encoding="utf-8")
CHANGELOG = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
FIXTURES = ROOT / "tests" / "fixtures"


class WorkflowContractTests(unittest.TestCase):
    def test_root_skill_keeps_the_complete_stage_chain(self) -> None:
        stages = [
            "Step 0：选择 Flash 或 Pro",
            "Step 1：识别会议模式和议题",
            "Step 2：执行 Boundary Guard",
            "Step 3：提取类别与约束",
            "Step 4：匹配专家",
            "Step 4.1：处理点名、排除和名单确认",
            "Step 4.5：加载人格",
            "Step 5：组织会议",
            "Step 5.5：四级综合",
            "Step 6：七类输出",
        ]
        offsets = [SKILL.index(stage) for stage in stages]
        self.assertEqual(offsets, sorted(offsets))

    def test_depth_and_confirmation_rules_are_explicit(self) -> None:
        for phrase in [
            "人类或程序化调用没有显式 Flash",
            "强制 Pro，覆盖 Flash",
            "必须展示名单并等待确认",
            "用户拒绝：提供“继续修改”或“取消会议”",
            "未收到确认：不得加载人格或生成专家发言",
        ]:
            self.assertIn(phrase, SKILL)

    def test_persona_fallback_branches_are_distinct(self) -> None:
        self.assertIn("单个文件不可读时", SKILL)
        self.assertIn("如果所有 Pro 人格都不可读", SKILL)
        self.assertIn("只有“全部 Pro 完整人格缺失”触发暂停确认", SKILL)

    def test_six_modes_and_mechanisms_are_present(self) -> None:
        for mode in ["共识", "对抗", "红队", "陪审团", "预审", "淬火"]:
            self.assertRegex(SKILL, rf"#### {mode}\n")
        self.assertIn("2–3 轮", SKILL)
        self.assertIn("各自说明认可对方至少一点", SKILL)
        self.assertIn("挑刺必须由未参加初议的专家执行", SKILL)
        self.assertIn("不是会议模式", SKILL)

    def test_organizer_and_seven_part_outer_contract(self) -> None:
        self.assertIn("不得产生独立专家观点或替用户作价值选择", SKILL)
        for number, title in [
            (1, "边界声明"),
            (2, "会议信息"),
            (3, "专家独立发言"),
            (4, "模式结果"),
            (5, "综合"),
            (6, "条件化行动选项"),
            (7, "结尾提醒"),
        ]:
            self.assertRegex(SKILL, rf"{number}\. {title}")
        self.assertIn("只限制模式分析段", SKILL)

    def test_obsolete_runtime_rules_are_absent(self) -> None:
        for phrase in ["结论优先", "Phase 5", "discussion"]:
            self.assertNotIn(phrase, SKILL)

    def test_default_enablement_is_consistent(self) -> None:
        self.assertIn("default-enabled: false", SKILL)
        self.assertIn("default-enabled: false", BRAIN_SKILL)
        self.assertIn("default-enabled: false", README)
        self.assertIn("default-enabled: false", CHANGELOG)

    def test_eight_baseline_prompts_are_preserved(self) -> None:
        prompts = json.loads(
            (FIXTURES / "workflow-prompts.json").read_text(encoding="utf-8")
        )
        self.assertEqual(list(range(1, 9)), [item["id"] for item in prompts])
        self.assertEqual(
            {
                "consensus",
                "red-team",
                "jury",
                "tempering",
                "pre-mortem",
                "debate",
                "reject",
            },
            {item["mode"] for item in prompts},
        )
        for item in prompts:
            self.assertIn("boundary_action", item["assertions"])

    def test_eight_prompts_execute_their_structured_script_contracts(self) -> None:
        prompts = json.loads(
            (FIXTURES / "workflow-prompts.json").read_text(encoding="utf-8")
        )
        category_map = {
            1: "内容,传播,增长",
            2: "战略,风险",
            3: "团队,决策",
            4: "战略,团队,成本",
            5: "投资,并购,风险",
            6: "产品,战略",
        }
        boundary_script = ROOT / "scripts" / "boundary-guard.py"
        match_script = ROOT / "scripts" / "match-experts.py"
        registry = ROOT / "brain-crew" / "expert-registry.json"
        for item in prompts:
            boundary = subprocess.run(
                [sys.executable, str(boundary_script), item["prompt"]],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            boundary_result = json.loads(boundary.stdout)
            self.assertEqual(
                item["assertions"]["boundary_action"],
                boundary_result["action"],
                item["id"],
            )
            if "boundary_domain" in item["assertions"]:
                self.assertEqual(
                    item["assertions"]["boundary_domain"],
                    boundary_result["domain"],
                )
            if item["id"] not in category_map:
                continue
            matched = subprocess.run(
                [
                    sys.executable,
                    str(match_script),
                    "--registry",
                    str(registry),
                    "--topic",
                    item["prompt"],
                    "--mode",
                    item["mode"],
                    "--categories",
                    category_map[item["id"]],
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            panel = json.loads(matched.stdout)["selected_panel"]
            self.assertGreaterEqual(
                len(panel),
                item["assertions"].get("min_experts", 3),
                item["id"],
            )

    def test_responsibility_map_and_conflict_allowlist_are_complete(self) -> None:
        responsibility = json.loads(
            (FIXTURES / "baseline" / "responsibility-map.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(10, len(responsibility["stages"]))
        for stage in responsibility["stages"]:
            if stage["stage"] not in {
                "expert_scoring_and_ranking",
                "boundary_classification",
                "regression_and_asset_validation",
            }:
                self.assertEqual(stage["baseline_owner"], stage["target_owner"])
        allowlist = json.loads(
            (FIXTURES / "baseline" / "conflict-allowlist.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(list(range(1, 25)), [item["id"] for item in allowlist["decisions"]])

    def test_no_forbidden_runtime_controller_modules_exist(self) -> None:
        forbidden = {
            "routing.py",
            "control.py",
            "validation.py",
            "meeting-control.py",
            "meeting_control.py",
        }
        found = {
            path.name
            for path in ROOT.rglob("*.py")
            if "tests" not in path.parts and path.name in forbidden
        }
        self.assertEqual(set(), found)

    def test_current_product_material_uses_40_experts_and_five_packs(self) -> None:
        current = "\n".join(
            [
                README,
                SKILL,
                BRAIN_SKILL,
                (ROOT / "brain-crew" / "README.md").read_text(encoding="utf-8"),
            ]
        )
        self.assertNotRegex(current, r"\b(?:34|39)\s*位专家")
        self.assertNotRegex(current, r"\b6\s*个\s*pack")
        self.assertIn("40 位专家", current)
        self.assertTrue(
            "5 个 pack" in current or "五个 pack" in current
        )


if __name__ == "__main__":
    unittest.main()
