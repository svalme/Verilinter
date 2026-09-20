from typing import TYPE_CHECKING

from ...parser.syntax import (
    comparison_operands,
    constant_integer_value,
    natural_expression_width_and_signed,
    unwrap_parentheses,
)
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _comparison_width_mismatch(vnode: BaseVNode, ctx: "Context") -> tuple[int, int] | None:
    """Return `(left_width, right_width)` if `vnode` is a comparison expression
    whose operand widths are known and differ, or where one operand is a known width
    and the other is a constant integer literal outside that operand's representable
    range.
    """
    raw = vnode.raw
    operands = comparison_operands(raw)
    if operands is None:
        return None
    left, right, _op = operands
    if left is None or right is None:
        return None

    scope = ctx.scope() if callable(getattr(ctx, "scope", None)) else None

    wl, sl_l = natural_expression_width_and_signed(scope, left, vnode.tree)
    wr, sl_r = natural_expression_width_and_signed(scope, right, vnode.tree)

    # Case A: Both operand widths are known
    if isinstance(wl, int) and isinstance(wr, int):
        if wl != wr:
            return wl, wr
        return None

    # Case B: Left operand width is known, right operand is a constant integer literal
    if isinstance(wl, int) and wl > 0:
        val = constant_integer_value(unwrap_parentheses(right))
        if val is not None:
            is_signed = bool(sl_l)
            if not is_signed:
                # Unsigned representable range: [0, 2^wl - 1]
                if val < 0:
                    req_bits = max(1, abs(val).bit_length()) + 1
                    return wl, req_bits
                if val.bit_length() > wl:
                    return wl, max(1, val.bit_length())
            else:
                # Signed representable range: [-2^(wl-1), 2^(wl-1) - 1]
                min_val = -(1 << (wl - 1))
                max_val = (1 << (wl - 1)) - 1
                if val < min_val or val > max_val:
                    req_bits = max(1, abs(val).bit_length()) + 1
                    return wl, req_bits

    # Case C: Right operand width is known, left operand is a constant integer literal
    if isinstance(wr, int) and wr > 0:
        val = constant_integer_value(unwrap_parentheses(left))
        if val is not None:
            is_signed = bool(sl_r)
            if not is_signed:
                # Unsigned representable range: [0, 2^wr - 1]
                if val < 0:
                    req_bits = max(1, abs(val).bit_length()) + 1
                    return req_bits, wr
                if val.bit_length() > wr:
                    return max(1, val.bit_length()), wr
            else:
                # Signed representable range: [-2^(wr-1), 2^(wr-1) - 1]
                min_val = -(1 << (wr - 1))
                max_val = (1 << (wr - 1)) - 1
                if val < min_val or val > max_val:
                    req_bits = max(1, abs(val).bit_length()) + 1
                    return req_bits, wr

    return None


@rule_runner.register
class ComparisonWidthMismatchRule(Rule):
    code = "COMPARISON_WIDTH_MISMATCH"
    message = "Comparison operands have mismatched bit widths"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _comparison_width_mismatch(vnode, ctx) is not None
