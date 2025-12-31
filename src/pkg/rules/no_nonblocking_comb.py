import pyslang as sl

from ..ast.context import ContextFlag
from .base_rule import Rule
from .rule_runner import rule_runner

@rule_runner.register
class NoNonBlockingAssignmentInCombRule(Rule):
    code = "NO_NONBLOCKING_COMBINATIONAL"
    message = "Non-blocking assignment used in combinational logic"

    def applies(self, vnode, ctx) -> bool:
        return vnode.raw.kind == sl.TokenKind.LessThanEquals and ctx.has(ContextFlag.ALWAYS_COMB)

