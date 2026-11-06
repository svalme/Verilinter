from typing import TYPE_CHECKING

from ...parser.syntax import (
    comparison_operands,
    constant_integer_value,
    identifier_name,
    natural_expression_width_and_signed,
    unwrap_parentheses,
)
from ...parser.types import BinaryExpressionNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context

_RELATIONAL = {"<", "<=", ">", ">="}
_EQUALITY = {"==", "!=", "===", "!==", "==?", "!=?"}


def _non_negative_constant(expr: object) -> bool:
    value = constant_integer_value(unwrap_parentheses(expr))
    return value is not None and value >= 0


def _is_constant_symbol(scope: object, expr: object) -> bool:
    """True for a parameter or enum member, whose signedness follows its value or type rather than a declaration."""
    name = identifier_name(unwrap_parentheses(expr))
    lookup = getattr(scope, "lookup_hierarchical", None)
    symbol = lookup(name) if name and callable(lookup) else None
    return getattr(symbol, "kind", None) in ("parameter", "enum_member")


def _comparison_signedness_mismatch(vnode: BaseVNode, ctx: "Context") -> bool:
    operands = comparison_operands(vnode.raw)
    if operands is None:
        return False
    left, right, op = operands
    if left is None or right is None or op not in _RELATIONAL | _EQUALITY:
        return False
    # A non-negative constant has the same value read as signed or unsigned.
    if _non_negative_constant(left) or _non_negative_constant(right):
        return False

    scope = ctx.scope() if callable(getattr(ctx, "scope", None)) else None
    if _is_constant_symbol(scope, left) or _is_constant_symbol(scope, right):
        return False
    width_l, signed_l = natural_expression_width_and_signed(scope, left, vnode.tree)
    width_r, signed_r = natural_expression_width_and_signed(scope, right, vnode.tree)
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
