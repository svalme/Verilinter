"""Keeps docs/FIXTURE_USAGE.md in sync with the actual fixture references in tests/.

To regenerate after adding, removing, or renaming a reference to a
tests/data/ fixture:

    UPDATE_EXPECTED=1 pytest tests/test_fixture_usage_doc.py

This mirrors the golden-file convention in tests/walk/print_tree_test.py: the
overwrite is a deliberate, reviewable diff rather than a doc that silently
drifts from reality.
"""

import os
from pathlib import Path

from .support.fixture_usage import collect_fixture_usage, render_fixture_usage_doc

DOC_PATH = Path(__file__).parent.parent / "docs" / "FIXTURE_USAGE.md"


def test_fixture_usage_doc_matches_current_references() -> None:
    actual = render_fixture_usage_doc(collect_fixture_usage())

    if os.environ.get("UPDATE_EXPECTED"):
        DOC_PATH.write_text(actual, encoding="utf-8")
        return

    assert DOC_PATH.exists(), f"Missing {DOC_PATH}; generate it with UPDATE_EXPECTED=1"
    expected = DOC_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        f"{DOC_PATH} is out of date with current fixture references. "
        f"Regenerate with: UPDATE_EXPECTED=1 pytest {Path(__file__).name}"
    )
