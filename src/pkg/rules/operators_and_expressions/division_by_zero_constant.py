from typing import TYPE_CHECKING

from ...parser.syntax import binary_operands, constant_integer_value, is_divide_or_mod_expression
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _is_division_by_zero_constant(raw: object) -> bool:
    if not is_divide_or_mod_expression(raw):
        return False
    operands = binary_operands(raw)
    if operands is None:
        return False
    _left, right = operands
    return constant_integer_value(right) == 0


@rule_runner.register
class DivisionByZeroConstantRule(Rule):
    code = "DIVISION_BY_ZERO_CONSTANT"
    message = "Division or modulo by a constant zero divisor"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        return _is_division_by_zero_constant(vnode.raw)
