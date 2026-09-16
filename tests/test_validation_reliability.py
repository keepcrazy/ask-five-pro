from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.support import temporary_file_replacement


ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "tests" / "run-validation.py"
REGISTRY = ROOT / "brain-crew" / "expert-registry.json"
ASSET_VALIDATOR = ROOT / "brain-crew" / "scripts" / "validate-expert-assets.py"


class ValidationReliabilityTests(unittest.TestCase):
    def test_aggregate_failure_returns_non_zero(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--self-test-failure"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertNotEqual(0, completed.returncode)
        self.assertIn("intentional validation failure", completed.stderr)

    def test_registry_replacement_restores_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "expert-registry.json"
            original = REGISTRY.read_bytes()
            path.write_bytes(original)
            with temporary_file_replacement(path, b'{"experts": []}\n'):
                self.assertNotEqual(original, path.read_bytes())
            self.assertEqual(original, path.read_bytes())

    def test_registry_replacement_restores_after_assertion_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "expert-registry.json"
            original = REGISTRY.read_bytes()
            path.write_bytes(original)
            with self.assertRaises(AssertionError):
                with temporary_file_replacement(path, b'{"experts": []}\n'):
                    raise AssertionError("deliberate")
            self.assertEqual(original, path.read_bytes())

    def test_registry_replacement_restores_after_exception(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            path = Path(raw_tmp) / "expert-registry.json"
            original = REGISTRY.read_bytes()
            path.write_bytes(original)
            with self.assertRaises(RuntimeError):
                with temporary_file_replacement(path, b'{"experts": []}\n'):
                    raise RuntimeError("deliberate")
            self.assertEqual(original, path.read_bytes())

    def test_asset_validator_is_cwd_independent(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            completed = subprocess.run(
                [sys.executable, str(ASSET_VALIDATOR)],
                cwd=raw_tmp,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["ok"])

    def test_historical_evidence_is_not_a_current_test_package(self) -> None:
        evidence = ROOT / "tests" / "evidence"
        self.assertTrue((evidence / "README.md").is_file())
        manifest = (evidence / "MANIFEST.md").read_text(encoding="utf-8")
        self.assertIn("4627911", manifest)
        self.assertIn("not a current test result", manifest)
        self.assertFalse(any(evidence.rglob("test_*.py")))


if __name__ == "__main__":
    unittest.main()
