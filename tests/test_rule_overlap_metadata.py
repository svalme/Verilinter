"""Structural guardrail for the `overlaps_with` metadata on rule classes.

`overlaps_with` (see `BaseDiagnostic`) is purely declarative: it has no runtime
effect. Its only job is to let a rule author record "this can plausibly co-fire
with (or must be suppressed relative to) that other rule" right next to the
rule's own code, instead of that fact living only in a contributor's head or in
a markdown doc no one is forced to open.

This file is what actually makes the declaration mean something: every declared
pair must (a) name a real, registered rule code, and (b) have at least one test
in `tests/test_rule_overlap_harness.py` that exercises both codes together. That
closes the gap docs/RULE_IMPLEMENTATION.md's Testing standard describes -- a
declared overlap can no longer silently lose its regression coverage.
"""

from __future__ import annotations

import ast
from pathlib import Path

from src.pkg.rules.base_diagnostic import BaseDiagnostic
from src.pkg.rules.register_rules import module_rule_runner, rule_runner, symbol_rule_runner

OVERLAP_HARNESS_PATH = Path(__file__).parent / "test_rule_overlap_harness.py"


def _all_rules() -> list[BaseDiagnostic]:
    return [*rule_runner._rules, *symbol_rule_runner._rules, *module_rule_runner._rules]


def _string_constants_by_test_function(source: str) -> dict[str, set[str]]:
    tree = ast.parse(source)
    by_function: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            by_function[node.name] = {
                child.value
                for child in ast.walk(node)
                if isinstance(child, ast.Constant) and isinstance(child.value, str)
            }
    return by_function


def test_overlaps_with_only_references_known_rule_codes() -> None:
    rules = _all_rules()
    codes = {rule.code for rule in rules}

    unknown = [f"{rule.code} -> {other!r}" for rule in rules for other in rule.overlaps_with if other not in codes]

    assert not unknown, "overlaps_with references code(s) with no registered rule (typo?): " + ", ".join(unknown)


def test_declared_overlaps_have_a_regression_test_in_the_overlap_harness() -> None:
    strings_by_test = _string_constants_by_test_function(OVERLAP_HARNESS_PATH.read_text(encoding="utf-8"))

    missing = {
        f"{rule.code} <-> {other}"
        for rule in _all_rules()
        for other in rule.overlaps_with
        if not any({rule.code, other}.issubset(strings) for strings in strings_by_test.values())
    }

    assert not missing, (
        "these rule pairs declare overlaps_with but no test in "
        f"{OVERLAP_HARNESS_PATH.name} exercises both codes together: " + ", ".join(sorted(missing))
    )
