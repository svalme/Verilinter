from __future__ import annotations

from src.pkg.parser.syntax_kinds import (
    BLOCKING_EVENT_TRIGGER_STATEMENT_KIND,
    CASE_STATEMENT_KIND,
    CONDITIONAL_STATEMENT_KIND,
    CONTINUOUS_ASSIGN_KIND,
    NONBLOCKING_EVENT_TRIGGER_STATEMENT_KIND,
    PRIMITIVE_INSTANTIATION_KIND,
)
from src.pkg.walk.context import Context
from tests.support.fakes import FakeVNode, fake_vnode


def token_vnode(kind: object) -> FakeVNode:
    return fake_vnode(kind)


def case_context(*, unique_or_priority: str | None = None) -> Context:
    return Context().push(fake_vnode(CASE_STATEMENT_KIND, uniqueOrPriority=unique_or_priority))


def case_inside_context(inside_token: object) -> Context:
    """A CaseStatement ancestor whose `matchesOrInside` is `inside_token`.

    Mirrors `case (expr) inside ... endcase`, where pyslang exposes the
    `inside` keyword as the case statement's own `matchesOrInside` field
    rather than as a token nested inside an ordinary expression.
    """
    return Context().push(fake_vnode(CASE_STATEMENT_KIND, matchesOrInside=inside_token))


def conditional_context(*, unique_or_priority: str | None = None) -> Context:
    return Context().push(fake_vnode(CONDITIONAL_STATEMENT_KIND, uniqueOrPriority=unique_or_priority))


def continuous_assign_context() -> Context:
    return Context().push(fake_vnode(CONTINUOUS_ASSIGN_KIND))


def primitive_instantiation_context() -> Context:
    return Context().push(fake_vnode(PRIMITIVE_INSTANTIATION_KIND))


def event_trigger_statement_context(*, nonblocking: bool = False) -> Context:
    kind = NONBLOCKING_EVENT_TRIGGER_STATEMENT_KIND if nonblocking else BLOCKING_EVENT_TRIGGER_STATEMENT_KIND
    return Context().push(fake_vnode(kind))


__all__ = [
    "case_context",
    "case_inside_context",
    "conditional_context",
    "continuous_assign_context",
    "event_trigger_statement_context",
    "primitive_instantiation_context",
    "token_vnode",
]
