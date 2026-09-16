from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class PortableInstallationTests(unittest.TestCase):
    def test_complete_skill_works_from_an_external_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as raw_tmp:
            tmp = Path(raw_tmp)
            install = tmp / "installed-skill"
            outside = tmp / "outside-cwd"
            install.mkdir()
            outside.mkdir()
            for file_name in ["SKILL.md", "README.md", "CHANGELOG.md"]:
                shutil.copy2(ROOT / file_name, install / file_name)
            for directory in ["brain-crew", "scripts", "references"]:
                shutil.copytree(ROOT / directory, install / directory)

            env = os.environ.copy()
            env.pop("BRAIN_CREW_REGISTRY", None)
            env.pop("RUNTIME_SKILLS_DIR", None)
            check = subprocess.run(
                ["bash", str(install / "scripts" / "check-experts.sh"), str(install)],
                cwd=outside,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(0, check.returncode, check.stdout + check.stderr)
            report = json.loads(check.stdout)
            self.assertEqual(40, len(report["installed"]))
            self.assertEqual([], report["simulated"])

            boundary = subprocess.run(
                [
                    sys.executable,
                    str(install / "scripts" / "boundary-guard.py"),
                    "我们要不要做短视频矩阵？",
                ],
                cwd=outside,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            self.assertEqual("analyze", json.loads(boundary.stdout)["action"])

            matched = subprocess.run(
                [
                    sys.executable,
                    str(install / "scripts" / "match-experts.py"),
                    "--registry",
                    str(install / "brain-crew" / "expert-registry.json"),
                    "--topic",
                    "产品路线如何取舍",
                    "--categories",
                    "产品",
                ],
                cwd=outside,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            self.assertGreaterEqual(
                len(json.loads(matched.stdout)["selected_panel"]),
                3,
            )

            assets = subprocess.run(
                [
                    sys.executable,
                    str(install / "brain-crew" / "scripts" / "validate-expert-assets.py"),
                    "--installed-only",
                ],
                cwd=outside,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(0, assets.returncode, assets.stdout + assets.stderr)
            self.assertEqual(40, json.loads(assets.stdout)["experts_checked"])


if __name__ == "__main__":
    unittest.main()
