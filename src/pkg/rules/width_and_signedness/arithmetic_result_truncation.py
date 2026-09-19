from typing import TYPE_CHECKING

from ...parser.syntax import (
    is_add_subtract_expression,
    is_multiply_expression,
    natural_expression_width_and_signed,
    resolve_assignment_target_and_rhs,
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
    if not is_add_subtract_expression(rhs) and not is_multiply_expression(rhs):
        return None

    width, _signed = natural_expression_width_and_signed(ctx.scope(), rhs, vnode.tree)
    return width


def _arithmetic_result_truncation(vnode: BaseVNode, ctx: "Context") -> bool:
    symbol, right = resolve_assignment_target_and_rhs(vnode, ctx)
    if symbol is None or right is None or not isinstance(symbol.bit_width, int):
        return False
    if getattr(symbol, "is_sliced", False):
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
