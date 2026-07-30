from ...parser.syntax import is_nonblocking_assignment_token
from ...vnodes.base_vnode import BaseVNode
from ...walk.context import Context, ContextFlag
from ..base_rule import Rule
from .rule_runner import rule_runner

@rule_runner.register
class NoNonBlockingAssignmentInCombRule(Rule):
    code = "NO_NONBLOCKING_COMBINATIONAL"
    message = "Non-blocking assignment used in combinational logic"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
        return is_nonblocking_assignment_token(vnode.raw) and ctx.has(ContextFlag.ALWAYS_COMB)
