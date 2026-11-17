"""Every per-node rule is tested against its nearest construct: some `clean` breadth case reaches the rule's check.

See `tests/support/breadth_reach.py`. A rule whose target node exists only for the construct itself is listed in
`CONSTRUCT_NODE_RULES` and is checked the other way: a listed rule that a `clean` case does reach is a stale entry.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.support.breadth_catalog import BREADTH_ROOT, parse_breadth_cases
from tests.support.breadth_reach import CONSTRUCT_NODE, NOT_PER_NODE, REACHES, reach_status

CODES = sorted(path.stem for path in BREADTH_ROOT.rglob("*.sv"))


@pytest.mark.parametrize("code", CODES)
def test_a_clean_case_reaches_the_rules_check(code: str) -> None:
    path = next(BREADTH_ROOT.rglob(f"{code}.sv"))
    status = reach_status(code, parse_breadth_cases(Path(path)))
    assert status in (REACHES, CONSTRUCT_NODE, NOT_PER_NODE), (
        f"{code}: {status}. Add a `clean` case that contains the construct nearest to the banned one (see "
        "tests/support/breadth_reach.py), or, when the rule's target node exists only for the construct, list the rule "
        "in CONSTRUCT_NODE_RULES."
    )
