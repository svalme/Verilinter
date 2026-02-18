import pyslang as sl

from ..vnodes.base_vnode import BaseVNode
from ..ast.context import Context, ContextFlag
from .base_rule import Rule
from .rule_runner import rule_runner

@rule_runner.register
class NoBlockingAssignmentInSequentialRule(Rule):
    code = "NO_BLOCKING_SEQUENTIAL"
    message = "Blocking assignment used in sequential logic"

    def applies(self, vnode, ctx) -> bool:
        return vnode.raw.kind == sl.TokenKind.Equals and ctx.has(ContextFlag.ALWAYS)

    