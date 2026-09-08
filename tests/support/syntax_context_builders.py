from __future__ import annotations

from unittest.mock import Mock

import pyslang as sl

from src.pkg.vnodes.base_vnode import BaseVNode
from src.pkg.walk.context import Context


def token_vnode(kind: object) -> Mock:
    vnode = Mock(spec=BaseVNode)
    vnode.raw = Mock()
    vnode.raw.kind = kind
    return vnode


def case_context(*, unique_or_priority: str | None = None) -> Context:
    vnode = Mock(spec=BaseVNode)
    vnode.raw = Mock()
    vnode.raw.kind = sl.SyntaxKind.CaseStatement
    vnode.raw.uniqueOrPriority = unique_or_priority
    return Context().push(vnode)


def case_inside_context(inside_token: object) -> Context:
    """A CaseStatement ancestor whose `matchesOrInside` is `inside_token`.

    Mirrors `case (expr) inside ... endcase`, where pyslang exposes the
    `inside` keyword as the case statement's own `matchesOrInside` field
    rather than as a token nested inside an ordinary expression.
    """
    vnode = Mock(spec=BaseVNode)
    vnode.raw = Mock()
    vnode.raw.kind = sl.SyntaxKind.CaseStatement
    vnode.raw.matchesOrInside = inside_token
    return Context().push(vnode)


def conditional_context(*, unique_or_priority: str | None = None) -> Context:
    vnode = Mock(spec=BaseVNode)
    vnode.raw = Mock()
    vnode.raw.kind = sl.SyntaxKind.ConditionalStatement
    vnode.raw.uniqueOrPriority = unique_or_priority
    return Context().push(vnode)


def continuous_assign_context() -> Context:
    vnode = Mock(spec=BaseVNode)
    vnode.raw = Mock()
    vnode.raw.kind = sl.SyntaxKind.ContinuousAssign
    return Context().push(vnode)


def primitive_instantiation_context() -> Context:
    vnode = Mock(spec=BaseVNode)
    vnode.raw = Mock()
    vnode.raw.kind = sl.SyntaxKind.PrimitiveInstantiation
    return Context().push(vnode)


def event_trigger_statement_context(*, nonblocking: bool = False) -> Context:
    vnode = Mock(spec=BaseVNode)
    vnode.raw = Mock()
    vnode.raw.kind = (
        sl.SyntaxKind.NonblockingEventTriggerStatement if nonblocking else sl.SyntaxKind.BlockingEventTriggerStatement
    )
    return Context().push(vnode)


__all__ = [
    "case_context",
    "case_inside_context",
    "conditional_context",
    "continuous_assign_context",
    "event_trigger_statement_context",
    "primitive_instantiation_context",
    "token_vnode",
]
