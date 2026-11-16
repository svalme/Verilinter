"""Runs every case in the catalog: a `reports` case must give the expected number of findings of its rule
(otherwise the rule is too narrow), a `clean` case must give none (otherwise it is too broad), and a `gap`
case is a known miss that must keep failing until the rule is fixed and the case is promoted to `reports`."""
from __future__ import annotations

import pytest

from tests.support.lint_harness import run_inline_lint_case
from tests.support.case_catalog import all_cases, parse_cases, KINDS

CASES = all_cases()


def _count(case) -> int:
    result = run_inline_lint_case({"top.sv": case.source})
    return sum(1 for d in result.diagnostics if d["code"] == case.rule)


@pytest.mark.parametrize("case", [s for s in CASES if s.kind != "gap"], ids=lambda s: s.id)
def test_case(case) -> None:
    found = _count(case)
    assert found == case.expect, (
        f"{case.rule} {'is too broad' if case.kind == 'clean' else 'is too narrow'}: "
        f"expected {case.expect} finding(s), got {found}. {case.title}"
    )


@pytest.mark.parametrize("case", [s for s in CASES if s.kind == "gap"], ids=lambda s: s.id)
@pytest.mark.xfail(strict=True, reason="known gap: promote this case to `reports` once the rule catches it")
def test_known_gap(case) -> None:
    assert _count(case) == case.expect


def test_every_case_names_its_pair_exactly_once() -> None:
    problems = []
    by_rule: dict[str, dict[str, list]] = {}
    for case in CASES:
        if case.pair:
            by_rule.setdefault(case.rule, {}).setdefault(case.pair, []).append(case.kind)
    for rule, pairs in by_rule.items():
        for name, kinds in pairs.items():
            if sorted(kinds) != ["clean", "reports"]:
                problems.append(f"{rule}: pair {name!r} must be one `reports` and one `clean`, found {kinds}")
    assert not problems, "\n".join(problems)


def test_case_kinds_are_known() -> None:
    assert all(s.kind in KINDS for s in CASES)
