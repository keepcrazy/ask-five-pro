#!/usr/bin/env python3
"""Backward-compatible entrypoint for the current validation suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent / "run-validation.py"
raise SystemExit(subprocess.call([sys.executable, str(SCRIPT)]))
