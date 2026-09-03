from ...parser.syntax import (
    enclosing_combinational_style_always_block,
    is_nonblocking_assignment_token,
)
from ...vnodes.base_vnode import BaseVNode
from ...walk.context import Context, ContextFlag
from ..base_rule import Rule
from ..rule_runner import rule_runner

@rule_runner.register
class NoNonBlockingAssignmentInCombRule(Rule):
    code = "NO_NONBLOCKING_COMBINATIONAL"
    message = "Non-blocking assignment used in combinational logic"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
        if not is_nonblocking_assignment_token(vnode.raw):
            return False
        # `always_comb` is the SystemVerilog-only spelling; classic Verilog writes the
        # same combinational intent as a plain `always @*` / `always @(*)` / `always
        # @(a or b)` block, which parses to a generic AlwaysBlock and never sets
        # ContextFlag.ALWAYS_COMB. Without this, the same bug shape went uncaught in
        # any file that can't use `always_comb`.
        return ctx.has(ContextFlag.ALWAYS_COMB) or enclosing_combinational_style_always_block(ctx) is not None
