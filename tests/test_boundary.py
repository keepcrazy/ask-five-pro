from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "boundary-guard.py"
FIXTURE = ROOT / "tests" / "fixtures" / "baseline" / "boundary-cases.json"


class BoundaryRegressionTests(unittest.TestCase):
    def test_baseline_results_are_field_for_field_identical(self) -> None:
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for case in fixture["cases"]:
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), case["prompt"]],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            self.assertEqual(case["result"], json.loads(completed.stdout))

    def test_multi_domain_uses_first_match(self) -> None:
        prompt = "这个合同涉及投资，今天必须决定"
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), prompt],
            text=True,
            stdout=subprocess.PIPE,
            check=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual("legal", result["domain"])
        self.assertEqual(["合同"], result["matched_keywords"])


if __name__ == "__main__":
    unittest.main()
