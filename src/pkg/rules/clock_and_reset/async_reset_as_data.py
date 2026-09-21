from typing import TYPE_CHECKING

from ...parser.syntax import is_async_reset_read_as_data
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class AsyncResetAsDataRule(Rule):
    code = "ASYNC_RESET_AS_DATA"
    message = "Asynchronous reset signal read as a data operand"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_async_reset_read_as_data(vnode, ctx)
