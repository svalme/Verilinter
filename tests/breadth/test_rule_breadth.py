"""Runs every breadth case in the catalog: a `reports` breadth case must give the expected number of findings of its rule
(otherwise the rule is too narrow), a `clean` breadth case must give none (otherwise it is too broad), and a `gap`
breadth case is a known miss that must keep failing until the rule is fixed and the breadth case is promoted to `reports`."""
from __future__ import annotations

import pytest

from tests.support.lint_harness import run_inline_lint_case
from tests.support.breadth_catalog import all_breadth_cases, parse_breadth_cases, KINDS

BREADTH_CASES = all_breadth_cases()


def _count(breadth) -> int:
    result = run_inline_lint_case({"top.sv": breadth.source})
    return sum(1 for d in result.diagnostics if d["code"] == breadth.rule)


@pytest.mark.parametrize("breadth", [s for s in BREADTH_CASES if s.kind != "gap"], ids=lambda s: s.id)
def test_case(breadth) -> None:
    found = _count(breadth)
    assert found == breadth.expect, (
        f"{breadth.rule} {'is too broad' if breadth.kind == 'clean' else 'is too narrow'}: "
        f"expected {breadth.expect} finding(s), got {found}. {breadth.title}"
    )


@pytest.mark.parametrize("breadth", [s for s in BREADTH_CASES if s.kind == "gap"], ids=lambda s: s.id)
@pytest.mark.xfail(strict=True, reason="known gap: promote this breadth case to `reports` once the rule catches it")
def test_known_gap(breadth) -> None:
    assert _count(breadth) == breadth.expect


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
