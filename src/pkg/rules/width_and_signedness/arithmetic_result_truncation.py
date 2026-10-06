from typing import TYPE_CHECKING

from ...parser.syntax import (
    simple_expression_width_and_signed,
    natural_expression_width_and_signed,
    resolve_assignment_target_and_rhs,
)
from ...parser.types import BinaryExpressionNode, DeclaratorNode, ImplicitAnsiPortNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _natural_result_width(vnode: BaseVNode, ctx: "Context", rhs: object) -> int | None:
    """Recover nested arithmetic capacity, conservatively skipping unknowns."""
    width, _signed = natural_expression_width_and_signed(ctx.scope(), rhs, vnode.tree)
    return width


def _arithmetic_result_truncation(vnode: BaseVNode, ctx: "Context") -> bool:
    symbol, right = resolve_assignment_target_and_rhs(vnode, ctx)
    if symbol is None or right is None or not isinstance(symbol.bit_width, int):
        return False
    # Ordinary value transfers belong to ASSIGNMENT_TRUNCATION. Keep direct
    # arithmetic here; for typed wrappers require additional product capacity.
    operand_width, _ = simple_expression_width_and_signed(ctx.scope(), right, vnode.tree)
    result_width = _natural_result_width(vnode, ctx, right)
    if result_width is None or (operand_width is not None and result_width <= operand_width):
        return False

    return result_width > symbol.bit_width


@rule_runner.register
class ArithmeticResultTruncationRule(Rule):
    """Flag recoverable arithmetic capacity exceeding the effective target.

    Full-product capacity is a lint policy, distinct from language expression
    sizing. Nested arithmetic and ternary branches are supported. Casts are
    explicit boundaries; addition carry-out is outside this policy.
    """

    code = "ARITHMETIC_RESULT_TRUNCATION"
    message = "Arithmetic result is wider than its assignment target, causing implicit truncation"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (BinaryExpressionNode, DeclaratorNode, ImplicitAnsiPortNode)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _arithmetic_result_truncation(vnode, ctx)
