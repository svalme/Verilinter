"""Meta-test keeping the name-only ways of reading an assignment out of consumers.

An assignment is read through `assignment_view` (syntax only) or `assignment_record` (with symbols,
driver and statement). The bare left and right accessors drop what the view and the record keep: the
selectors of a target, the members of a concatenation, the kind of assignment. Only the two modules
that build the view and the access-mode walk below them may use those accessors.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"

BANNED_NAMES = {"assignment_left", "assignment_right", "assignment_target_identifier_name"}

ALLOWED_FILES = {
    "pkg/parser/_syntax_queries/access.py",
    "pkg/parser/_syntax_queries/assignment_records.py",
}


def _mentions(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom):
            found.update(alias.name for alias in node.names if alias.name in BANNED_NAMES)
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            found.add(node.id)
        elif isinstance(node, ast.Attribute) and node.attr in BANNED_NAMES:
            found.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in BANNED_NAMES:
            found.add(node.value)
    return found


def test_bare_assignment_accessors_stay_inside_the_view_modules() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        rel = path.relative_to(SRC_ROOT).as_posix()
        if rel in ALLOWED_FILES:
            continue
        violations.extend(f"{rel}: {name}" for name in sorted(_mentions(path)))
    assert not violations, (
        "Read an assignment through assignment_view or assignment_record, not the bare accessors:\n"
        + "\n".join(violations)
    )
