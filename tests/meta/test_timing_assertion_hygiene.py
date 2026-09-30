"""Meta-test keeping wall-clock budget checks inside the termination harness.

A bare `assert time.perf_counter() - t0 < 0.05` fails with two raw numbers and
no hint whether the code regressed or the machine was busy. Budget checks go
through `tests.support.termination.terminates_within`.
"""
from __future__ import annotations

import ast
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parents[1]
HARNESS = TESTS_ROOT / "support" / "termination.py"
CLOCK_FUNCTIONS = {"perf_counter", "perf_counter_ns", "monotonic", "monotonic_ns", "time", "time_ns"}


def test_wall_clock_budgets_use_the_termination_harness() -> None:
    violations: list[str] = []
    for path in sorted(TESTS_ROOT.rglob("test_*.py")):
        if path == HARNESS or any(part.startswith("_tmp") for part in path.parts):
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "time"
                and node.func.attr in CLOCK_FUNCTIONS
            ):
                violations.append(f"{path.relative_to(TESTS_ROOT).as_posix()}:{node.lineno}: time.{node.func.attr}()")
    assert not violations, (
        "Use `with terminates_within(...)` from tests/support/termination.py for time budgets:\n"
        + "\n".join(violations)
    )
