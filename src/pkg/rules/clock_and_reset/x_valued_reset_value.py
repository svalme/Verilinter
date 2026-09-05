from typing import TYPE_CHECKING

from ...parser.syntax import is_explicit_xz_literal, is_within_async_reset_conditional
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class AsyncResetXZValueRule(Rule):
    code = "ASYNC_RESET_XZ_VALUE"
    message = "Explicit X/Z literal assigned inside an async-reset conditional, defeating reset determinism"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("EXPLICIT_XZ_LITERAL",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_explicit_xz_literal(vnode.raw) and is_within_async_reset_conditional(ctx)
