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


def conditional_context(*, unique_or_priority: str | None = None) -> Context:
    vnode = Mock(spec=BaseVNode)
    vnode.raw = Mock()
    vnode.raw.kind = sl.SyntaxKind.ConditionalStatement
    vnode.raw.uniqueOrPriority = unique_or_priority
    return Context().push(vnode)


__all__ = ["case_context", "conditional_context", "token_vnode"]
