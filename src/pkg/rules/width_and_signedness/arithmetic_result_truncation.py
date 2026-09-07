from typing import TYPE_CHECKING

from ...parser.syntax import (
    assignment_left,
    assignment_right,
    binary_operands,
    identifier_name,
    is_add_subtract_expression,
    is_assignment_expression,
    is_multiply_expression,
    simple_expression_width_and_signed,
)
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _natural_result_width(vnode: BaseVNode, ctx: "Context", rhs: object) -> int | None:
    """Return the natural (self-determined) result width of `rhs` if it is a
    `+`/`-`/`*` binary expression whose two operands both have independently
    recoverable widths, else `None`. Add/subtract follows Verilog's
    self-determined-context width rule (`max` of the two operand widths,
    ignoring any carry-out bit); multiply is the sum of the two operand
    widths. Only a direct binary expression is considered -- a richer
    expression (nested arithmetic, a ternary, a reduction) is silently
    skipped rather than guessed at, the same recoverability posture as
    `ASSIGNMENT_WIDTH_MISMATCH`.
    """
    is_add_sub = is_add_subtract_expression(rhs)
    is_mul = is_multiply_expression(rhs)
    if not is_add_sub and not is_mul:
        return None

    operands = binary_operands(rhs)
    if operands is None:
        return None
    left, right = operands

    left_width, _left_signed = simple_expression_width_and_signed(ctx.scope(), left, vnode.tree)
    right_width, _right_signed = simple_expression_width_and_signed(ctx.scope(), right, vnode.tree)
    if not isinstance(left_width, int) or not isinstance(right_width, int):
        return None

    return left_width + right_width if is_mul else max(left_width, right_width)


def _arithmetic_result_truncation(vnode: BaseVNode, ctx: "Context") -> bool:
    if not is_assignment_expression(vnode.raw):
        return False
    left = assignment_left(vnode.raw)
    right = assignment_right(vnode.raw)
    if left is None or right is None:
        return False

    name = identifier_name(left)
    if name is None:
        return False
    symbol = ctx.scope().lookup(name)
    if symbol is None or not isinstance(symbol.bit_width, int):
        return False

    result_width = _natural_result_width(vnode, ctx, right)
    if result_width is None:
        return False

    return result_width > symbol.bit_width


@rule_runner.register
class ArithmeticResultTruncationRule(Rule):
    """Flags a simple identifier assignment target whose declared width is
    narrower than the natural (self-determined) result width of a direct
    `+`/`-`/`*` right-hand side -- e.g. `wire [7:0] p; assign p = a * b;`
    where `a`/`b` are both 8-bit, so the true 16-bit product is silently
    truncated. Distinct from `ASSIGNMENT_WIDTH_MISMATCH`/`ASSIGNMENT_TRUNCATION`,
    which never fire here: `simple_expression_width_and_signed` has no binary-
    operator case at all, so an arithmetic RHS is invisible to those rules --
    this rule is the one place that width is actually inferred.
    """

    code = "ARITHMETIC_RESULT_TRUNCATION"
    message = "Arithmetic result is wider than its assignment target, causing implicit truncation"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _arithmetic_result_truncation(vnode, ctx)
