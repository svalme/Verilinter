from typing import TYPE_CHECKING

from ...parser.syntax import (
    binary_operands,
    constant_integer_value,
    is_shift_expression,
    simple_expression_width_and_signed,
)
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _shift_amount_out_of_range(vnode: BaseVNode, ctx: "Context") -> bool:
    """True when `vnode` is a shift expression whose constant shift amount is
    negative or `>=` the shifted operand's declared width. Fires when the
    shifted operand has a recoverable width (via `simple_expression_width_and_signed`)
    and the shift amount is itself a recoverable compile-time constant.
    """
    if not is_shift_expression(vnode.raw):
        return False
    operands = binary_operands(vnode.raw)
    if operands is None:
        return False
    left, right = operands

    amount = constant_integer_value(right)
    if amount is None:
        return False

    left_width, _ = simple_expression_width_and_signed(ctx.scope(), left, vnode.tree)
    if not isinstance(left_width, int):
        return False

    return amount < 0 or amount >= left_width


@rule_runner.register
class ShiftAmountOutOfRangeRule(Rule):
    code = "SHIFT_AMOUNT_OUT_OF_RANGE"
    message = "Constant shift amount is negative or exceeds the shifted operand's declared width"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _shift_amount_out_of_range(vnode, ctx)
