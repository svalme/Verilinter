"""Keeps the breadth coverage table in docs/TESTING.md in sync with the files in tests/breadth/.

To regenerate after adding, removing or changing a breadth file:

    UPDATE_EXPECTED=1 pytest tests/meta/test_breadth_catalog_doc.py
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.support.breadth_coverage import BEGIN_MARKER, END_MARKER, render_coverage_block

pytestmark = pytest.mark.meta

DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "TESTING.md"


def _split(text: str) -> tuple[str, str, str]:
    start = text.index(BEGIN_MARKER)
    end = text.index(END_MARKER) + len(END_MARKER)
    return text[:start], text[start:end], text[end:]


def test_breadth_coverage_table_matches_case_files() -> None:
    text = DOC_PATH.read_bytes().decode("utf-8")
    assert BEGIN_MARKER in text and END_MARKER in text, f"{DOC_PATH.name} lacks the breadth coverage markers"
    before, current, after = _split(text)
    actual = render_coverage_block()

    if os.environ.get("UPDATE_EXPECTED"):
        DOC_PATH.write_bytes((before + actual + after).encode("utf-8"))
        return

    assert current == actual, (
        f"The breadth coverage table in {DOC_PATH.name} is out of date. "
        f"Regenerate with: UPDATE_EXPECTED=1 pytest tests/meta/{Path(__file__).name}"
    )
