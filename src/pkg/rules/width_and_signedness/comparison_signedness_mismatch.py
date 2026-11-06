from typing import TYPE_CHECKING

from ...parser.syntax import comparison_operands
from ...parser.types import BinaryExpressionNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner
from .operand import classify_operand

if TYPE_CHECKING:
    from ...walk.context import Context

_RELATIONAL = {"<", "<=", ">", ">="}
_EQUALITY = {"==", "!=", "===", "!==", "==?", "!=?"}


def _comparison_signedness_mismatch(vnode: BaseVNode, ctx: "Context") -> bool:
    operands = comparison_operands(vnode.raw)
    if operands is None:
        return False
    left, right, op = operands
    if left is None or right is None or op not in _RELATIONAL | _EQUALITY:
        return False
    scope = ctx.scope() if callable(getattr(ctx, "scope", None)) else None
    operand_l = classify_operand(scope, left, vnode.tree)
    operand_r = classify_operand(scope, right, vnode.tree)
    # A non-negative constant has the same value read as signed or unsigned.
    if any(o.is_literal and o.value >= 0 for o in (operand_l, operand_r)):
        return False
    if operand_l.is_constant_symbol or operand_r.is_constant_symbol:
        return False
    width_l, signed_l = operand_l.width, operand_l.signed
    width_r, signed_r = operand_r.width, operand_r.signed
    if signed_l is None or signed_r is None or signed_l == signed_r:
        return False
    if op in _RELATIONAL:
        return True
    # Equal-width operands compare identically as signed or unsigned bit patterns.
    return isinstance(width_l, int) and isinstance(width_r, int) and width_l != width_r


@rule_runner.register
class ComparisonSignednessMismatchRule(Rule):
    code = "COMPARISON_SIGNEDNESS_MISMATCH"
    message = "Comparison mixes signed and unsigned operands"
    category = "rtl_correctness"
    confidence = "heuristic"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (BinaryExpressionNode,)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _comparison_signedness_mismatch(vnode, ctx)
