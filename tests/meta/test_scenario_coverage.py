"""Meta-test: every rule has a scenario file with what it must report and what it must not.

A rule changed without scenarios can drift too narrow or too broad unnoticed. `tests/scenarios/<category>/<CODE>.sv`
holds, per rule, at least one `reports` and one `clean` scenario (see `tests/support/scenario_catalog.py`).
`tests/scenarios/PENDING_RULES.txt` lists the rules that have no file yet: it only shrinks. A new rule is not added
to it; it comes with its scenario file.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from src.pkg.rules.register_rules import module_rule_runner, rule_runner, symbol_rule_runner
from tests.support.scenario_catalog import SCENARIO_ROOT, all_scenario_files, parse_scenarios

pytestmark = pytest.mark.meta

PENDING_FILE = SCENARIO_ROOT / "PENDING_RULES.txt"


def _registered() -> dict[str, str]:
    """rule code -> category folder (`src/pkg/rules/<category>/...`)."""
    registered: dict[str, str] = {}
    for runner in (rule_runner, symbol_rule_runner, module_rule_runner):
        for rule in runner._rules:
            registered[rule.code] = type(rule).__module__.split(".")[3]
    return registered


def _pending() -> set[str]:
    return {line.strip() for line in PENDING_FILE.read_text(encoding="utf-8").splitlines() if line.strip()}


def test_every_rule_has_scenarios_or_is_listed_as_pending() -> None:
    have = {p.stem for p in all_scenario_files()}
    missing = sorted(set(_registered()) - have - _pending())
    assert not missing, (
        "These rules have no scenario file. Add tests/scenarios/<category>/<CODE>.sv with at least one `reports` and "
        "one `clean` scenario (do not add the rule to PENDING_RULES.txt):\n" + "\n".join(missing)
    )


def test_pending_list_only_names_rules_that_still_lack_a_file() -> None:
    registered = set(_registered())
    have = {p.stem for p in all_scenario_files()}
    stale = sorted(code for code in _pending() if code not in registered or code in have)
    assert not stale, "Remove from PENDING_RULES.txt (unknown rule, or its scenario file now exists):\n" + "\n".join(stale)


def test_scenario_files_sit_in_their_rule_category_and_have_both_kinds() -> None:
    registered = _registered()
    problems = []
    for path in all_scenario_files():
        code = path.stem
        if code not in registered:
            problems.append(f"{path.name}: no registered rule with this code")
            continue
        if path.parent.name != registered[code]:
            problems.append(f"{path.name}: belongs in tests/scenarios/{registered[code]}/")
        kinds = {s.kind for s in parse_scenarios(path)}
        for needed in ("reports", "clean"):
            if needed not in kinds:
                problems.append(f"{path.name}: needs at least one `{needed}` scenario")
    assert not problems, "\n".join(problems)
