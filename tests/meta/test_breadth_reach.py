"""The breadth reach tool: which clean cases are judged by a rule and which are quiet because they hold no node it inspects."""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.support.breadth_catalog import BreadthCase
from tests.support.breadth_reach import clean_cases_reaching_the_check, node_rule_class

pytestmark = pytest.mark.meta


def _case(kind: str, title: str, source: str) -> BreadthCase:
    return BreadthCase("NO_TASK_DECLARATION", kind, title, source, 0 if kind == "clean" else 1, None, Path("x.sv"))


NEAREST = _case(
    "clean",
    "A function declaration is not a task declaration.",
    "module top(output logic o); function automatic logic f(input logic a); return a; endfunction assign o = f(1'b0); endmodule",
)
VACUOUS = _case(
    "clean",
    "The word task in a comment does not declare one.",
    "module top(input logic a, output logic o); // task is banned\n assign o = a;\nendmodule",
)
REPORTED = _case(
    "reports",
    "A task declaration is reported.",
    "module top(output logic o); task automatic t(input logic a); o = a; endtask endmodule",
)


def test_a_clean_case_with_the_nearest_construct_reaches_the_check_and_a_comment_does_not() -> None:
    reaching, quiet = clean_cases_reaching_the_check("NO_TASK_DECLARATION", [NEAREST, VACUOUS, REPORTED])  # type: ignore[misc]
    assert reaching == [NEAREST]
    assert quiet == [VACUOUS]


def test_only_clean_cases_are_counted() -> None:
    reaching, quiet = clean_cases_reaching_the_check("NO_TASK_DECLARATION", [REPORTED])  # type: ignore[misc]
    assert reaching == [] and quiet == []


def test_a_rule_that_does_not_decide_per_node_is_skipped() -> None:
    assert node_rule_class("NO_SUCH_RULE") is None
    assert clean_cases_reaching_the_check("NO_SUCH_RULE", [NEAREST]) is None


def test_the_rule_decides_as_before_once_the_check_is_done() -> None:
    clean_cases_reaching_the_check("NO_TASK_DECLARATION", [NEAREST])
    from tests.support.lint_harness import run_inline_lint_case

    function = run_inline_lint_case({"top.sv": NEAREST.source})
    task = run_inline_lint_case({"top.sv": REPORTED.source})
    assert not [d for d in function.diagnostics if d["code"] == "NO_TASK_DECLARATION"]
    assert len([d for d in task.diagnostics if d["code"] == "NO_TASK_DECLARATION"]) == 1
