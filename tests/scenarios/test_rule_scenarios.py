"""Runs every scenario in the catalog: a `reports` scenario must give the expected number of findings of its rule
(otherwise the rule is too narrow), a `clean` scenario must give none (otherwise it is too broad), and a `gap`
scenario is a known miss that must keep failing until the rule is fixed and the scenario is promoted to `reports`."""
from __future__ import annotations

import pytest

from tests.support.lint_harness import run_inline_lint_case
from tests.support.scenario_catalog import all_scenarios, parse_scenarios, KINDS

SCENARIOS = all_scenarios()


def _count(scenario) -> int:
    result = run_inline_lint_case({"top.sv": scenario.source})
    return sum(1 for d in result.diagnostics if d["code"] == scenario.rule)


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if s.kind != "gap"], ids=lambda s: s.id)
def test_scenario(scenario) -> None:
    found = _count(scenario)
    assert found == scenario.expect, (
        f"{scenario.rule} {'is too broad' if scenario.kind == 'clean' else 'is too narrow'}: "
        f"expected {scenario.expect} finding(s), got {found}. {scenario.title}"
    )


@pytest.mark.parametrize("scenario", [s for s in SCENARIOS if s.kind == "gap"], ids=lambda s: s.id)
@pytest.mark.xfail(strict=True, reason="known gap: promote this scenario to `reports` once the rule catches it")
def test_known_gap(scenario) -> None:
    assert _count(scenario) == scenario.expect


def test_every_scenario_names_its_pair_exactly_once() -> None:
    problems = []
    by_rule: dict[str, dict[str, list]] = {}
    for scenario in SCENARIOS:
        if scenario.pair:
            by_rule.setdefault(scenario.rule, {}).setdefault(scenario.pair, []).append(scenario.kind)
    for rule, pairs in by_rule.items():
        for name, kinds in pairs.items():
            if sorted(kinds) != ["clean", "reports"]:
                problems.append(f"{rule}: pair {name!r} must be one `reports` and one `clean`, found {kinds}")
    assert not problems, "\n".join(problems)


def test_scenario_kinds_are_known() -> None:
    assert all(s.kind in KINDS for s in SCENARIOS)
