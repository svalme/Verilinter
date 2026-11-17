"""Which `clean` breadth cases of a node rule reach the rule's check.

A `clean` case is quiet for one of two reasons: the rule looked at the code and judged it fine, or the code holds no
node the rule inspects. Only the first shows the rule tells a construct from its neighbor. To tell them apart, the
rule's `applies` decision is inverted for the run: a `clean` case that then reports reached the check, and one that
stays quiet never did. A rule none of whose `clean` cases reach the check is not tested on its boundary.

    python -m tests.support.breadth_reach NO_TASK_DECLARATION NO_INITIAL_BLOCK
"""
from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from tests.support.breadth_catalog import BreadthCase, parse_breadth_cases
from tests.support.lint_harness import run_inline_lint_case


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


def main(codes: list[str]) -> int:
    breadth_root = Path(__file__).resolve().parents[1] / "breadth"
    weak = 0
    for code in codes:
        path = next(iter(breadth_root.rglob(f"{code}.sv")), None)
        if path is None:
            print(f"{code}: no breadth file")
            continue
        outcome = clean_cases_reaching_the_check(code, parse_breadth_cases(path))
        if outcome is None:
            print(f"{code}: not a per-node rule, skipped")
            continue
        reaching, quiet = outcome
        flag = "" if reaching else "   <- no clean case reaches the check"
        weak += 0 if reaching else 1
        print(f"{code}: {len(reaching)} of {len(reaching) + len(quiet)} clean cases reach the check{flag}")
    return 1 if weak else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
