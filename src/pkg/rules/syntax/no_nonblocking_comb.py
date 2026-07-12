from ...parser.syntax import is_nonblocking_assignment_token
from ...walk.context import ContextFlag
from ..base_rule import Rule
from .rule_runner import rule_runner

@rule_runner.register
class NoNonBlockingAssignmentInCombRule(Rule):
    code = "NO_NONBLOCKING_COMBINATIONAL"
    message = "Non-blocking assignment used in combinational logic"

    def applies(self, vnode, ctx) -> bool:
        return is_nonblocking_assignment_token(vnode.raw) and ctx.has(ContextFlag.ALWAYS_COMB)
