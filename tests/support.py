"""Test-only helpers. Nothing in this module participates in product runtime."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def temporary_file_replacement(path: Path, replacement: bytes) -> Iterator[None]:
    original = path.read_bytes()
    try:
        path.write_bytes(replacement)
        yield
    finally:
        path.write_bytes(original)
