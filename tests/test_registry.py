from __future__ import annotations

import importlib
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BRAIN = ROOT / "brain-crew"
REGISTRY = BRAIN / "expert-registry.json"
OLD_REGISTRY = ROOT / "references" / "expert-registry.json"
sys.path.insert(0, str(BRAIN / "scripts"))
query = importlib.import_module("brain_crew_query")


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    block = text.split("---", 2)[1]
    values = {}
    for line in block.splitlines():
        if line and not line[0].isspace() and not line.startswith("-") and ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip("'\"")
    return values


class RegistryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.experts = cls.data["experts"]

    def test_single_registry_and_legacy_path_removed(self) -> None:
        self.assertTrue(REGISTRY.is_file())
        self.assertFalse(OLD_REGISTRY.exists())
        self.assertFalse(Path(str(OLD_REGISTRY) + ".bak").exists())
        with self.assertRaises(FileNotFoundError):
            query.find_registry_path(OLD_REGISTRY)

    def test_counts_and_pack_distribution(self) -> None:
        self.assertEqual(40, len(self.experts))
        self.assertEqual(40, len({expert["id"] for expert in self.experts}))
        packs = {}
        for expert in self.experts:
            packs[expert["pack"]] = packs.get(expert["pack"], 0) + 1
        self.assertEqual(
            {"core": 6, "brand": 10, "tech": 7, "enterprise": 12, "meta": 5},
            packs,
        )

    def test_registry_fields_are_normalized(self) -> None:
        for expert in self.experts:
            self.assertIn("default_enabled", expert)
            self.assertNotIn("bundled", expert)
            path = Path(expert["path"])
            self.assertFalse(path.is_absolute())
            self.assertNotIn("..", path.parts)

    def test_registry_diff_contains_only_approved_normalization(self) -> None:
        baseline = json.loads(
            subprocess.check_output(
                ["git", "show", "4627911:brain-crew/expert-registry.json"],
                cwd=ROOT,
                text=True,
            )
        )
        missing_defaults = [
            expert["id"]
            for expert in baseline["experts"]
            if "default_enabled" not in expert
        ]
        bundled_count = sum("bundled" in expert for expert in baseline["experts"])
        self.assertEqual(
            [
                "jeff-bezos",
                "kazuo-inamori",
                "wang-yangming",
                "duan-yongping",
                "jensen-huang",
            ],
            missing_defaults,
        )
        self.assertEqual(6, bundled_count)

        expected = json.loads(json.dumps(baseline))
        for expert in expected["experts"]:
            prefix = "<runtime-skills-dir>/brain-crew/"
            if expert["path"].startswith(prefix):
                expert["path"] = expert["path"][len(prefix):]
            expert.setdefault("default_enabled", False)
            expert.pop("bundled", None)
        self.assertEqual(expected, self.data)

    def test_three_identifier_layers(self) -> None:
        for expert in self.experts:
            skill = BRAIN / expert["path"]
            self.assertTrue(skill.is_file(), expert["id"])
            meta = frontmatter(skill)
            self.assertEqual(expert["id"], meta.get("id"))
            self.assertEqual(skill.parent.name, meta.get("name"))
            self.assertIsInstance(expert["name"], str)
            self.assertTrue(expert["name"])

    def test_query_default_is_the_built_in_registry(self) -> None:
        loaded = query.load_registry()
        self.assertEqual(REGISTRY.resolve(), Path(loaded["_registry_path"]))


if __name__ == "__main__":
    unittest.main()
