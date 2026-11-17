"""Meta-test: every rule has a breadth file with what it must report and what it must not.

A rule changed without breadth cases can drift too narrow or too broad unnoticed. `tests/breadth/<category>/<CODE>.sv`
holds, per rule, at least one `reports` and one `clean` breadth case (see `tests/support/breadth_catalog.py`).
`tests/breadth/RULE_BREADTH_STATUS.txt` lists every rule with `yes` or `no` for whether it has a breadth file. A `no`
only ever becomes `yes`; a new rule is listed as `yes`, together with its breadth file.
"""
from __future__ import annotations

from collections import Counter

import pytest

from tests.support.breadth_catalog import all_breadth_files, parse_breadth_cases
from tests.support.breadth_coverage import listed_breadth_status as _listed, registered_categories as _registered

pytestmark = pytest.mark.meta


def test_every_rule_is_listed_once_in_the_breadth_status_list() -> None:
    codes = [code for code, _ in _listed()]
    registered = set(_registered())
    duplicates = sorted(code for code, n in Counter(codes).items() if n > 1)
    missing = sorted(registered - set(codes))
    unknown = sorted(set(codes) - registered)
    bad_status = sorted(code for code, status in _listed() if status not in ("yes", "no"))
    problems = (
        [f"listed more than once: {code}" for code in duplicates]
        + [f"not listed (add `{code} yes` with its breadth file): {code}" for code in missing]
        + [f"not a registered rule: {code}" for code in unknown]
        + [f"status must be `yes` or `no`: {code}" for code in bad_status]
    )
    assert not problems, "tests/breadth/RULE_BREADTH_STATUS.txt:\n" + "\n".join(problems)


def test_breadth_status_list_matches_the_breadth_files() -> None:
    have = {p.stem for p in all_breadth_files()}
    problems = []
    for code, status in _listed():
        if status == "yes" and code not in have:
            problems.append(f"{code} is listed `yes` but tests/breadth/<category>/{code}.sv does not exist")
        if status == "no" and code in have:
            problems.append(f"{code} has a breadth file: change its line to `{code} yes`")
    assert not problems, "tests/breadth/RULE_BREADTH_STATUS.txt:\n" + "\n".join(problems)


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
