"""Meta-test: every rule has a breadth file with what it must report and what it must not.

A rule changed without breadth cases can drift too narrow or too broad unnoticed. `tests/breadth/<category>/<CODE>.sv`
holds, per rule, at least one `reports` and one `clean` breadth case (see `tests/support/breadth_catalog.py`).
`tests/breadth/PENDING_RULES.txt` lists the rules that have no file yet: it only shrinks. A new rule is not added
to it; it comes with its breadth file.
"""
from __future__ import annotations

import pytest

from tests.support.breadth_catalog import all_breadth_files, parse_breadth_cases
from tests.support.breadth_coverage import pending_rules as _pending, registered_categories as _registered

pytestmark = pytest.mark.meta


def test_every_rule_has_breadth_cases_or_is_listed_as_pending() -> None:
    have = {p.stem for p in all_breadth_files()}
    missing = sorted(set(_registered()) - have - _pending())
    assert not missing, (
        "These rules have no breadth file. Add tests/breadth/<category>/<CODE>.sv with at least one `reports` and "
        "one `clean` breadth case (do not add the rule to PENDING_RULES.txt):\n" + "\n".join(missing)
    )


def test_pending_list_only_names_rules_that_still_lack_a_file() -> None:
    registered = set(_registered())
    have = {p.stem for p in all_breadth_files()}
    stale = sorted(code for code in _pending() if code not in registered or code in have)
    assert not stale, "Remove from PENDING_RULES.txt (unknown rule, or its breadth file now exists):\n" + "\n".join(stale)


def test_breadth_files_sit_in_their_rule_category_and_have_both_kinds() -> None:
    registered = _registered()
    problems = []
    for path in all_breadth_files():
        code = path.stem
        if code not in registered:
            problems.append(f"{path.name}: no registered rule with this code")
            continue
        if path.parent.name != registered[code]:
            problems.append(f"{path.name}: belongs in tests/breadth/{registered[code]}/")
        kinds = {s.kind for s in parse_breadth_cases(path)}
        for needed in ("reports", "clean"):
            if needed not in kinds:
                problems.append(f"{path.name}: needs at least one `{needed}` breadth case")
    assert not problems, "\n".join(problems)
