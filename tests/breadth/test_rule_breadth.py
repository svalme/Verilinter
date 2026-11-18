"""Runs every breadth case in the catalog: a `reports` breadth case must give the expected number of findings of its rule
(otherwise the rule is too narrow), a `clean` breadth case must give none (otherwise it is too broad), and a `gap`
breadth case is a known miss that must keep failing until the rule is fixed and the breadth case is promoted to `reports`."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.pkg.engine import analyze

from src.pkg.parser.parse import text_uses_default_nettype_none
from tests.support.lint_harness import LintCaseFile, run_inline_lint_case_spec
from tests.support.breadth_catalog import all_breadth_cases, parse_breadth_cases, KINDS

BREADTH_CASES = all_breadth_cases()


# These rules read widths from slang's elaboration of the file set, which only the file-based entry point performs
# (the command line's path), so their breadth cases run through it.
ELABORATED_RULES = {"PORT_CONNECTION_WIDTH_MISMATCH", "PORT_CONNECTION_WIDTH_UNKNOWN"}


def _count_from_files(breadth, tmp_path: Path) -> int:
    path = tmp_path / "top.sv"
    path.write_bytes(breadth.source.encode("utf-8"))
    result = analyze([path], rule_profile="rtl_strict")
    return sum(1 for d in result.diagnostics if d["code"] == breadth.rule)


def _count(breadth, tmp_path: Path) -> int:
    if breadth.rule in ELABORATED_RULES:
        return _count_from_files(breadth, tmp_path)
    # The command line decides `default_nettype none` per file from its text; do the same here.
    case_file = LintCaseFile(breadth.source, default_nettype_none=text_uses_default_nettype_none(breadth.source))
    result = run_inline_lint_case_spec({"top.sv": case_file})
    return sum(1 for d in result.diagnostics if d["code"] == breadth.rule)


@pytest.mark.parametrize("breadth", [s for s in BREADTH_CASES if s.kind != "gap"], ids=lambda s: s.id)
def test_case(breadth, tmp_path: Path) -> None:
    found = _count(breadth, tmp_path)
    assert found == breadth.expect, (
        f"{breadth.rule} {'is too broad' if breadth.kind == 'clean' else 'is too narrow'}: "
        f"expected {breadth.expect} finding(s), got {found}. {breadth.title}"
    )


@pytest.mark.parametrize("breadth", [s for s in BREADTH_CASES if s.kind == "gap"], ids=lambda s: s.id)
@pytest.mark.xfail(strict=True, reason="known gap: promote this breadth case to `reports` (or `clean`, when it expects 0) once the rule behaves as expected")
def test_known_gap(breadth, tmp_path: Path) -> None:
    assert _count(breadth, tmp_path) == breadth.expect


def test_every_breadth_case_names_its_pair_exactly_once() -> None:
    problems = []
    by_rule: dict[str, dict[str, list]] = {}
    for breadth in BREADTH_CASES:
        if breadth.pair:
            by_rule.setdefault(breadth.rule, {}).setdefault(breadth.pair, []).append(breadth.kind)
    for rule, pairs in by_rule.items():
        for name, kinds in pairs.items():
            if sorted(kinds) != ["clean", "reports"]:
                problems.append(f"{rule}: pair {name!r} must be one `reports` and one `clean`, found {kinds}")
    assert not problems, "\n".join(problems)


def test_breadth_case_kinds_are_known() -> None:
    assert all(s.kind in KINDS for s in BREADTH_CASES)
