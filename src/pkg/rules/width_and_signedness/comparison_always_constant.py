from typing import TYPE_CHECKING

from ...parser.syntax import comparison_operands
from ...parser.types import BinaryExpressionNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner
from .operand import classify_operand

if TYPE_CHECKING:
    from ...walk.context import Context

# Operator as seen with the variable operand on the left -> mirrored operator when it is on the right.
_MIRRORED = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}


def _always_constant(op: str, constant: int, high: int, bounded: bool) -> bool:
    """True when `variable <op> constant` has one outcome for every value in `[0, high]`.

    Constants outside the range are reported by COMPARISON_WIDTH_MISMATCH, so only the boundary cases remain.
    The lower bound of an unsigned operand always holds; the upper bound needs a `bounded` operand.
    """
    if op == "<":
        return constant == 0
    if op == ">=":
        return constant == 0
    if not bounded:
        return False
    if op == "<=":
        return constant == high
    if op == ">":
        return constant == high
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
        limit = classify_operand(scope, constant_expr, vnode.tree)
        operand = classify_operand(scope, variable, vnode.tree)
        if not limit.is_literal or operand.is_constant_symbol:
            continue
        constant, width, signed = limit.value, operand.width, operand.signed
        if not isinstance(width, int) or width <= 0 or signed is not False:
            continue
        bounded = operand.is_width_bounded
        if 0 <= constant <= (1 << width) - 1 and _always_constant(effective_op, constant, (1 << width) - 1, bounded):
            return True
    return False


@rule_runner.register
class ComparisonAlwaysConstantRule(Rule):
    code = "COMPARISON_ALWAYS_CONSTANT"
    message = "Comparison of an unsigned operand against the limit of its range always has the same result"
    category = "rtl_correctness"
    confidence = "heuristic"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (BinaryExpressionNode,)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _comparison_always_constant(vnode, ctx)
