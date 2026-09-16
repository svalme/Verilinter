from typing import TYPE_CHECKING

from ...parser.syntax import (
    assignment_left,
    assignment_right,
    declarator_has_initializer,
    declarator_initializer_expression,
    declarator_is_parameter,
    declarator_name,
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


def _resolve_assignment_target_and_rhs(vnode: BaseVNode, ctx: "Context"):
    if is_assignment_expression(vnode.raw):
        left = assignment_left(vnode.raw)
        right = assignment_right(vnode.raw)
        if left is None or right is None:
            return None, None
        return _lhs_symbol(ctx, left), right

    if declarator_has_initializer(vnode.raw):
        if declarator_is_parameter(ctx):
            return None, None
        name = declarator_name(vnode.raw)
        if name is None:
            return None, None
        lhs_symbol = ctx.scope().lookup(name)
        right = declarator_initializer_expression(vnode.raw)
        return lhs_symbol, right

    return None, None


def _width_mismatch(vnode: BaseVNode, ctx: "Context") -> tuple[int, int] | None:
    """Return `(lhs_width, rhs_width)` when a simple assignment's recoverable
    right-hand-side width is known and differs from its target's declared
    width, else `None`.
    """
    lhs_symbol, right = _resolve_assignment_target_and_rhs(vnode, ctx)
    if lhs_symbol is None or right is None or not isinstance(lhs_symbol.bit_width, int):
        return None

    rhs_width, _rhs_signed = simple_expression_width_and_signed(ctx.scope(), right, vnode.tree)
    if not isinstance(rhs_width, int):
        return None

    if lhs_symbol.bit_width != rhs_width:
        return lhs_symbol.bit_width, rhs_width
    return None


def _signedness_mismatch(vnode: BaseVNode, ctx: "Context") -> tuple[bool, bool] | None:
    """Sign-mismatch sibling of `_width_mismatch`, same recoverability limits."""
    lhs_symbol, right = _resolve_assignment_target_and_rhs(vnode, ctx)
    if lhs_symbol is None or right is None or lhs_symbol.is_signed is None:
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


@rule_runner.register
class NoAssignmentTruncationRule(Rule):
    """Narrower, direction-specific sibling of `ASSIGNMENT_WIDTH_MISMATCH`:
    fires only when the right-hand side is wider than the target, the lossy
    (data-dropping) direction of a width mismatch, as opposed to a safe
    zero/sign-extending narrower-to-wider assignment. Always co-fires with
    `ASSIGNMENT_WIDTH_MISMATCH` on the same construct -- see `overlaps_with`
    and the matching regression case in `tests/test_rule_overlap_harness.py`.
    """

    code = "ASSIGNMENT_TRUNCATION"
    message = "Assignment right-hand side is wider than its target, causing implicit truncation"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("ASSIGNMENT_WIDTH_MISMATCH",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        widths = _width_mismatch(vnode, ctx)
        return widths is not None and widths[1] > widths[0]
