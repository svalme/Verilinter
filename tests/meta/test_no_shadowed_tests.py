"""A second class or test function with an existing name replaces the first one without any error."""
from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parents[1]


def _duplicates(body: list[ast.stmt]) -> list[str]:
    names = Counter(
        node.name for node in body if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    )
    return [name for name, count in names.items() if count > 1 and name.startswith(("Test", "test"))]


def test_no_test_class_or_function_is_defined_twice_in_the_same_scope() -> None:
    problems: list[str] = []
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(TESTS_DIR).as_posix()
        problems += [f"{relative}: {name}" for name in _duplicates(tree.body)]
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                problems += [f"{relative}: {node.name}.{name}" for name in _duplicates(node.body)]
    assert problems == [], "shadowed (silently replaced) tests:\n" + "\n".join(problems)
