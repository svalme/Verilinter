from typing import TYPE_CHECKING

from ...parser.syntax import (
    assignment_left,
    assignment_right,
    identifier_name,
    is_assignment_expression,
    simple_expression_width_and_signed,
)
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _lhs_symbol(ctx: "Context", left: object):
    name = identifier_name(left)
    if name is None:
        return None
    return ctx.scope().lookup(name)


def _width_mismatch(vnode: BaseVNode, ctx: "Context") -> tuple[int, int] | None:
    """Return `(lhs_width, rhs_width)` when a simple assignment's recoverable
    right-hand-side width is known and differs from its target's declared
    width, else `None`.

    First pass only covers a simple identifier left-hand side (the same
    scope as `NO_SELF_ASSIGNMENT`/`NO_UNSIZED_LITERAL`) and only fires when
    both sides' widths are independently recoverable via
    `simple_expression_width_and_signed` -- the same conservative
    "known vs. known" shape `PORT_CONNECTION_WIDTH_MISMATCH` already uses at
    instance boundaries, just applied to an ordinary in-module assignment
    instead of a port connection. An unsized literal RHS (`x = 5;`, already
    separately flagged by `NO_UNSIZED_LITERAL`) has no recoverable width, so
    it is silently skipped here rather than double-reported.
    """
    if not is_assignment_expression(vnode.raw):
        return None
    left = assignment_left(vnode.raw)
    right = assignment_right(vnode.raw)
    if left is None or right is None:
        return None

    lhs_symbol = _lhs_symbol(ctx, left)
    if lhs_symbol is None or not isinstance(lhs_symbol.bit_width, int):
        return None

    rhs_width, _rhs_signed = simple_expression_width_and_signed(ctx.scope(), right, vnode.tree)
    if not isinstance(rhs_width, int):
        return None

    if lhs_symbol.bit_width != rhs_width:
        return lhs_symbol.bit_width, rhs_width
    return None


def _signedness_mismatch(vnode: BaseVNode, ctx: "Context") -> tuple[bool, bool] | None:
    """Sign-mismatch sibling of `_width_mismatch`, same recoverability limits."""
    if not is_assignment_expression(vnode.raw):
        return None
    left = assignment_left(vnode.raw)
    right = assignment_right(vnode.raw)
    if left is None or right is None:
        return None

    lhs_symbol = _lhs_symbol(ctx, left)
    if lhs_symbol is None or lhs_symbol.is_signed is None:
        return None

    _rhs_width, rhs_signed = simple_expression_width_and_signed(ctx.scope(), right, vnode.tree)
    if rhs_signed is None:
        return None

    if bool(lhs_symbol.is_signed) != bool(rhs_signed):
        return bool(lhs_symbol.is_signed), bool(rhs_signed)
    return None


@rule_runner.register
class NoAssignmentWidthMismatchRule(Rule):
    code = "ASSIGNMENT_WIDTH_MISMATCH"
    message = "Assignment right-hand side width does not match its target's declared width"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _width_mismatch(vnode, ctx) is not None


@rule_runner.register
class NoAssignmentSignednessMismatchRule(Rule):
    code = "ASSIGNMENT_SIGNEDNESS_MISMATCH"
    message = "Assignment right-hand side signedness does not match its target's declared signedness"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _signedness_mismatch(vnode, ctx) is not None
