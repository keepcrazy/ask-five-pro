#!/usr/bin/env python3
"""Run all current Ask Five Pro validation layers."""

from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TEST_DIR.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--self-test-failure",
        action="store_true",
        help="return a deliberate non-zero status to test the aggregate gate",
    )
    args = parser.parse_args()
    if args.self_test_failure:
        print("intentional validation failure", file=sys.stderr)
        return 1

    suite = unittest.defaultTestLoader.discover(
        start_dir=str(TEST_DIR),
        pattern="test_*.py",
        top_level_dir=str(PROJECT_DIR),
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
