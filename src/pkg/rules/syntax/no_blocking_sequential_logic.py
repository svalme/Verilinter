from ...parser.syntax import is_blocking_assignment_token
from ...vnodes.base_vnode import BaseVNode
from ...walk.context import Context, ContextFlag
from ..base_rule import Rule
from .rule_runner import rule_runner

@rule_runner.register
class NoBlockingAssignmentInSequentialRule(Rule):
    code = "NO_BLOCKING_SEQUENTIAL"
    message = "Blocking assignment used in sequential logic"

    def applies(self, vnode, ctx) -> bool:
        return is_blocking_assignment_token(vnode.raw) and ctx.has(ContextFlag.ALWAYS)
