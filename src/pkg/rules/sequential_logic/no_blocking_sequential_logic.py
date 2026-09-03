from ...parser.syntax import (
    enclosing_combinational_style_always_block,
    is_blocking_assignment_token,
)
from ...vnodes.base_vnode import BaseVNode
from ...walk.context import Context, ContextFlag
from ..base_rule import Rule
from ..rule_runner import rule_runner

@rule_runner.register
class NoBlockingAssignmentInSequentialRule(Rule):
    code = "NO_BLOCKING_SEQUENTIAL"
    message = "Blocking assignment used in sequential logic"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
        if not is_blocking_assignment_token(vnode.raw):
            return False
        if not ctx.has(ContextFlag.ALWAYS):
            return False
        # ContextFlag.ALWAYS is set for every plain `always` block, edge-triggered or
        # not -- a combinational-style block (`always @*`, `always @(*)`, or a
        # non-edge explicit list like `always @(a or b)`) is classic Verilog's
        # combinational spelling, where `=` is the *correct* assignment style.
        # Flagging it would report entirely correct code as "blocking assignment
        # used in sequential logic".
        return enclosing_combinational_style_always_block(ctx) is None
