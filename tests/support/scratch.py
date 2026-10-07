"""Scratch directories that are removed when the creating test finishes.

Tests that need a real directory (SQLite stores, CLI output files, on-disk
HDL) must create it through ``make_scratch`` so that nothing survives to be
picked up by a later test or run. The autouse fixture in ``tests/conftest.py``
calls ``remove_registered`` after every test and ``sweep_roots`` once at
session start (for leftovers from a crashed run).

Set ``VERILINTER_KEEP_SCRATCH=1`` to keep directories for debugging.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import stat
import uuid

TESTS_ROOT = Path(__file__).resolve().parents[1]
_registered: list[Path] = []


def _rmtree(path: Path) -> None:
    """Remove a tree, clearing read-only flags that make Windows refuse deletion."""

    def _clear_and_retry(func, target, _exc) -> None:
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass

    shutil.rmtree(path, onexc=_clear_and_retry)


def keep_scratch() -> bool:
    return os.environ.get("VERILINTER_KEEP_SCRATCH") == "1"


def make_scratch(root_name: str, name: str) -> Path:
    """Create a unique directory under ``tests/<root_name>`` and register it."""
    root = TESTS_ROOT / root_name
    assert root_name.startswith("_tmp_"), "scratch roots must be named _tmp_*"
    target = root / f"{name}_{uuid.uuid4().hex}"
    target.mkdir(parents=True, exist_ok=False)
    _registered.append(target)
    return target


def remove_registered() -> None:
    if keep_scratch():
        _registered.clear()
        return
    while _registered:
        path = _registered.pop()
        path.resolve().relative_to(TESTS_ROOT)
        _rmtree(path)


def sweep_roots() -> None:
    """Delete the contents of every ``tests/_tmp_*`` root left by earlier runs."""
    if keep_scratch():
        return
    for root in TESTS_ROOT.glob("_tmp_*"):
        if root.is_dir():
            for child in root.iterdir():
                _rmtree(child) if child.is_dir() else child.unlink(missing_ok=True)
