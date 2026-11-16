"""Meta-test: no source or test module grows into a monolith.

A file that holds several concerns hides which one a lookup or helper belongs to, and a test file with dozens of
unrelated classes is hard to navigate and to keep in step with the rule it covers. Split by concern, and group the
pieces in a folder (`src/pkg/parser/_syntax_queries/expressions/`, `tests/cli/run_lint/`), instead of raising the limit.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]
MAX_LINES = 700

# A file that is long for a reason that does not make it several concerns: a generated or hand-kept table.
EXEMPT = {
    "src/pkg/parser/syntax_kinds.py": "one table of pyslang syntax and token kinds",
}


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def test_no_python_file_exceeds_the_size_limit() -> None:
    too_long = []
    for root in ("src", "tests"):
        for path in sorted((ROOT / root).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel in EXEMPT:
                continue
            lines = _line_count(path)
            if lines > MAX_LINES:
                too_long.append(f"{rel}: {lines} lines")
    assert not too_long, (
        f"These files are over {MAX_LINES} lines. Split each by concern into a folder of smaller modules "
        "(see docs/TESTING.md and docs/CONTRIBUTING.md) instead of raising the limit:\n" + "\n".join(too_long)
    )


def test_every_exempt_file_exists_and_is_still_over_the_limit() -> None:
    stale = [rel for rel in EXEMPT if not (ROOT / rel).exists() or _line_count(ROOT / rel) <= MAX_LINES]
    assert not stale, f"Remove from EXEMPT (gone or no longer long): {stale}"
