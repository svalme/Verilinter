"""Which `clean` breadth cases of a node rule reach the rule's check.

A `clean` case is quiet for one of two reasons: the rule looked at the code and judged it fine, or the code holds no
node the rule inspects. Only the first shows the rule tells a construct from its neighbor. To tell them apart, the
rule's `applies` decision is inverted for the run: a `clean` case that then reports reached the check, and one that
stays quiet never did. A rule none of whose `clean` cases reach the check is not tested on its boundary.

    python -m tests.support.breadth_reach NO_TASK_DECLARATION NO_INITIAL_BLOCK

The check does not apply to a rule whose target node type exists only when the construct is present (a class, a checker,
a specify block, a queue dimension): no neighbor can contain such a node, so the node type itself is the boundary and
`applies` is only `is_<that node>`. Those rules are listed in `CONSTRUCT_NODE_RULES`; the list is checked both ways.
"""
from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from tests.support.breadth_catalog import BreadthCase, parse_breadth_cases
from tests.support.lint_harness import run_inline_lint_case


# Per-node rules whose target node types exist only for the construct itself, so no `clean` case can reach the check.
CONSTRUCT_NODE_RULES = frozenset(
    {
        "NO_ALIAS_STATEMENT", "NO_BIND_DIRECTIVE", "NO_CASE_GENERATE", "NO_CHECKER_DECLARATION", "NO_CLASS_DECLARATION",
        "NO_CLOCKING_DECLARATION", "NO_CONCURRENT_ASSERTION", "NO_CONFIG_DECLARATION", "NO_COVERGROUP_DECLARATION",
        "NO_DELAY_CONTROL", "NO_DPI_IMPORT_EXPORT", "NO_GENERATE_FOR", "NO_IF_GENERATE", "NO_IMMEDIATE_ASSERTION",
        "NO_LET_DECLARATION", "NO_MODPORT_DECLARATION", "NO_PRIMITIVE_DECLARATION", "NO_PROPERTY_DECLARATION",
        "NO_QUEUE", "NO_RANDSEQUENCE", "NO_SEQUENCE_DECLARATION", "NO_SPECIFY_BLOCK", "NO_VIRTUAL_INTERFACE", "NULLPORT",
    }
)

REACHES = "reaches"
CONSTRUCT_NODE = "construct node"
NOT_PER_NODE = "not per-node"
WEAK = "no clean case reaches the check"
STALE = "listed as a construct node rule but a clean case reaches the check"


def _subclasses(cls: type) -> Iterator[type]:
    for sub in cls.__subclasses__():
        yield sub
        yield from _subclasses(sub)


def node_rule_class(code: str) -> type | None:
    """The node rule class with this code that decides per node with its own `applies`, or None."""
    import src.pkg.rules.register_rules  # noqa: F401  (registers every rule)
    from src.pkg.rules.base_rule import Rule

    for cls in _subclasses(Rule):
        if getattr(cls, "code", None) == code and "applies" in cls.__dict__:
            return cls
    return None


@contextmanager
def inverted_applies(rule_class: type) -> Iterator[None]:
    original = rule_class.__dict__["applies"]
    rule_class.applies = lambda self, vnode, ctx: not original(self, vnode, ctx)  # type: ignore[method-assign]
    try:
        yield
    finally:
        rule_class.applies = original  # type: ignore[method-assign]


def clean_cases_reaching_the_check(code: str, cases: list[BreadthCase]) -> tuple[list[BreadthCase], list[BreadthCase]] | None:
    """`(reaching, not reaching)` among the `clean` cases of the rule, or None when the rule has no per-node `applies`."""
    rule_class = node_rule_class(code)
    if rule_class is None:
        return None
    reaching: list[BreadthCase] = []
    quiet: list[BreadthCase] = []
    with inverted_applies(rule_class):
        for case in (c for c in cases if c.kind == "clean"):
            result = run_inline_lint_case({"top.sv": case.source})
            (reaching if any(d["code"] == code for d in result.diagnostics) else quiet).append(case)
    return reaching, quiet


def reach_status(code: str, cases: list[BreadthCase]) -> str:
    """One of REACHES, CONSTRUCT_NODE, NOT_PER_NODE, WEAK or STALE for the rule's `clean` cases."""
    outcome = clean_cases_reaching_the_check(code, cases)
    if outcome is None:
        return NOT_PER_NODE
    reaches = bool(outcome[0])
    if code in CONSTRUCT_NODE_RULES:
        return STALE if reaches else CONSTRUCT_NODE
    return REACHES if reaches else WEAK


def main(codes: list[str]) -> int:
    breadth_root = Path(__file__).resolve().parents[1] / "breadth"
    weak = 0
    for code in codes:
        path = next(iter(breadth_root.rglob(f"{code}.sv")), None)
        if path is None:
            print(f"{code}: no breadth file")
            continue
        status = reach_status(code, parse_breadth_cases(path))
        print(f"{code}: {status}")
        weak += status in (WEAK, STALE)
    return 1 if weak else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
