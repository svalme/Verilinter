"""Meta-tests for the isolation standards in docs/TESTING.md ("Isolation standards").

- Memoized results are keyed through `node_cache`, never a bare `id(node)`:
  pyslang wrappers are short-lived, so a recycled `id` returns another node's
  cached result (an intermittent wrong-diagnostic failure).
- Tests create on-disk scratch space through `make_scratch`, which registers it
  for removal after the test, never by hand under `tests/_tmp_*`.
"""
from __future__ import annotations

import ast
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = TESTS_ROOT.parent / "src" / "pkg"

# `id()` is legitimate for per-traversal visited sets (entries removed on exit
# or discarded with the traversal), for sets of long-lived registry objects
# (rules, scopes, contexts), and in node_cache itself, which pins the node.
ID_ALLOWLIST = {
    "rules/rule_runner.py",
    "semantic/symbol_table.py",
    "walk/context.py",
    "walk/walker.py",
    "parser/_syntax_queries/node_cache.py",
    "parser/_syntax_queries/expressions.py",
    "parser/_syntax_queries/shapes.py",
    "parser/_syntax_queries/procedural.py",
    "parser/traversal_guard.py",
}
SCRATCH_ALLOWLIST = {
    "conftest.py",
    "support/scratch.py",
    "support/lint_harness.py",
    # Asserts that the harness removes its own `_tmp_harness` case directories.
    "integration/test_rule_case_harness.py",
}


def _calls_id(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "id"


def test_id_is_not_used_as_a_cache_key_outside_node_cache() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        rel = path.relative_to(SRC_ROOT).as_posix()
        if rel in ID_ALLOWLIST:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if _calls_id(node):
                violations.append(f"{rel}:{node.lineno}")
    assert not violations, (
        "Key per-module memoization with parser/_syntax_queries/node_cache.py "
        "(node_cache_get/node_cache_put), not id(node):\n" + "\n".join(violations)
    )


def test_scratch_directories_are_created_through_make_scratch() -> None:
    violations: list[str] = []
    for path in sorted(TESTS_ROOT.rglob("*.py")):
        rel = path.relative_to(TESTS_ROOT).as_posix()
        if rel in SCRATCH_ALLOWLIST or rel.startswith("meta/") or any(p.startswith("_tmp") for p in path.parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        allowed = {
            id(arg)
            for call in ast.walk(tree)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "make_scratch"
            for arg in call.args
        }
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value.startswith("_tmp_")
                and id(node) not in allowed
            ):
                violations.append(f"{rel}:{node.lineno}: {node.value!r}")
    assert not violations, (
        "Create scratch space with tests.support.scratch.make_scratch so it is removed after the test:\n"
        + "\n".join(violations)
    )
