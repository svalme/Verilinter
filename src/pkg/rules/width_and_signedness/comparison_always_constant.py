from typing import TYPE_CHECKING

from ...parser.syntax import (
    comparison_operands,
    constant_integer_value,
    natural_expression_width_and_signed,
    unwrap_parentheses,
)
from ...parser.types import BinaryExpressionNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context

# Operator as seen with the variable operand on the left -> mirrored operator when it is on the right.
_MIRRORED = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}


def _always_constant(op: str, constant: int, high: int) -> bool:
    """True when `variable <op> constant` has one outcome for every value in `[0, high]`.

    Constants outside the range are reported by COMPARISON_WIDTH_MISMATCH, so only the boundary cases remain.
    """
    if op == "<":
        return constant == 0
    if op == "<=":
        return constant == high
    if op == ">":
        return constant == high
    if op == ">=":
        return constant == 0
    return False


def _comparison_always_constant(vnode: BaseVNode, ctx: "Context") -> bool:
    operands = comparison_operands(vnode.raw)
    if operands is None:
        return False
    left, right, op = operands
    if left is None or right is None or op not in _MIRRORED:
        return False

    scope = ctx.scope() if callable(getattr(ctx, "scope", None)) else None
    for variable, constant_expr, effective_op in ((left, right, op), (right, left, _MIRRORED[op])):
        constant = constant_integer_value(unwrap_parentheses(constant_expr))
        if constant is None:
            continue
        width, signed = natural_expression_width_and_signed(scope, variable, vnode.tree)
        if not isinstance(width, int) or width <= 0 or signed is not False:
            continue
        if 0 <= constant <= (1 << width) - 1 and _always_constant(effective_op, constant, (1 << width) - 1):
            return True
    return False


@rule_runner.register
class ComparisonAlwaysConstantRule(Rule):
    code = "COMPARISON_ALWAYS_CONSTANT"
    message = "Comparison of an unsigned operand against the limit of its range always has the same result"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (BinaryExpressionNode,)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _comparison_always_constant(vnode, ctx)
