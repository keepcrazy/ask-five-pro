from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BASELINE_DIR = ROOT / "tests" / "fixtures" / "baseline"
VALIDATOR = ROOT / "brain-crew" / "scripts" / "validate-expert-assets.py"


class ExpertAssetTests(unittest.TestCase):
    def test_full_source_comparison_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
        report = json.loads(completed.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual(40, report["experts_checked"])
        self.assertEqual(40, report["flash_profiles_checked"])
        self.assertGreaterEqual(report["source_files_checked"], 40)

    def test_source_map_covers_every_expert(self) -> None:
        source_map = json.loads(
            (BASELINE_DIR / "expert-source-map.json").read_text(encoding="utf-8")
        )
        self.assertEqual(40, len(source_map["experts"]))
        self.assertEqual(40, len({item["id"] for item in source_map["experts"]}))
        for item in source_map["experts"]:
            self.assertEqual("4627911", item["revision"])
            self.assertEqual("local-git:ask-five-pro", item["repository"])

    def test_missing_expert_asset_fails_the_gate(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            copied = Path(raw_tmp) / "brain-crew"
            shutil.copytree(ROOT / "brain-crew", copied)
            registry = json.loads(
                (copied / "expert-registry.json").read_text(encoding="utf-8")
            )
            missing = copied / registry["experts"][0]["path"]
            missing.unlink()
            completed = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--registry",
                    str(copied / "expert-registry.json"),
                    "--installed-only",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertNotEqual(0, completed.returncode)
        self.assertFalse(json.loads(completed.stdout)["ok"])

    def test_migration_map_covers_every_baseline_file_once(self) -> None:
        manifest = json.loads(
            (BASELINE_DIR / "file-manifest.json").read_text(encoding="utf-8")
        )
        migration = json.loads(
            (BASELINE_DIR / "migration-map.json").read_text(encoding="utf-8")
        )
        source_paths = [item["path"] for item in manifest["files"]]
        migration_sources = [item["source"] for item in migration["entries"]]
        self.assertEqual(145, len(source_paths))
        self.assertEqual(source_paths, migration_sources)
        self.assertEqual(len(migration_sources), len(set(migration_sources)))
        for item in migration["entries"]:
            self.assertIn(
                item["action"],
                {"keep", "move", "merge", "delete", "rewrite"},
            )
            self.assertTrue(item["reason"])

    def test_migration_map_matches_the_current_tree(self) -> None:
        migration = json.loads(
            (BASELINE_DIR / "migration-map.json").read_text(encoding="utf-8")
        )
        for item in migration["entries"]:
            source = ROOT / item["source"]
            target = ROOT / item["target"] if item["target"] else None
            if item["action"] in {"move", "merge"}:
                self.assertFalse(source.exists(), item)
                self.assertIsNotNone(target)
                self.assertTrue(target.exists(), item)
            elif item["action"] == "delete":
                self.assertFalse(source.exists(), item)
                self.assertIsNone(target)
            else:
                self.assertIsNotNone(target)
                self.assertTrue(target.exists(), item)

    def test_keep_and_move_actions_preserve_baseline_blobs(self) -> None:
        manifest = json.loads(
            (BASELINE_DIR / "file-manifest.json").read_text(encoding="utf-8")
        )
        baseline_blobs = {
            item["path"]: item["object_id"] for item in manifest["files"]
        }
        migration = json.loads(
            (BASELINE_DIR / "migration-map.json").read_text(encoding="utf-8")
        )
        for item in migration["entries"]:
            if item["action"] not in {"keep", "move"}:
                continue
            target = ROOT / item["target"]
            payload = target.read_bytes()
            git_blob = hashlib.sha1(
                f"blob {len(payload)}\0".encode("ascii") + payload
            ).hexdigest()
            self.assertEqual(baseline_blobs[item["source"]], git_blob, item)


if __name__ == "__main__":
    unittest.main()
