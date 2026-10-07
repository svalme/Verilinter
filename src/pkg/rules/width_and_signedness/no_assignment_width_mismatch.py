from typing import TYPE_CHECKING

from ...parser.syntax import (
    has_explicit_signedness_cast,
    element_select_index_or_range,
    evaluate_constant_text_expression,
    extract_assignment_target_and_selectors,
    resolve_assignment_target_and_rhs,
    simple_expression_width_and_signed,
)
from ...parser.traversal_guard import guarded_traversal
from ...parser._syntax_queries.node_cache import MISSING, node_cache_get, node_cache_put
from ...parser.types import (
    BinaryExpressionNode,
    DeclaratorNode,
    ImplicitAnsiPortNode,
    SyntaxNode,
)
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


def _check_index_selector_width_mismatch(
    selectors: list[object],
    symbol: object,
    ctx: "Context",
    tree: object,
) -> tuple[int, int] | None:
    if not selectors or symbol is None:
        return None
    scope = getattr(ctx, "scope", lambda: None)()
    if scope is None:
        return None
    unpacked_widths = list(getattr(symbol, "unpacked_dimension_widths", []))
    if not unpacked_widths and getattr(symbol, "unpacked_dimensions", None):
        for msb_txt, lsb_txt in symbol.unpacked_dimensions:
            m = None
            l = None
            try:
                m = int(msb_txt)
            except (ValueError, TypeError):
                m = evaluate_constant_text_expression(msb_txt, scope=scope)
            try:
                l = int(lsb_txt)
            except (ValueError, TypeError):
                l = evaluate_constant_text_expression(lsb_txt, scope=scope)

            if isinstance(m, int) and isinstance(l, int):
                unpacked_widths.append(abs(m - l) + 1)
            else:
                unpacked_widths.append(None)
    for i, sel in enumerate(selectors):
        if i < len(unpacked_widths):
            dim_w = unpacked_widths[i]
            if isinstance(dim_w, int) and dim_w > 1:
                req_bits = max(1, (dim_w - 1).bit_length())
                unwrapped = element_select_index_or_range(sel)
                if unwrapped is not None and unwrapped[0] == "bit":
                    idx_w, _ = simple_expression_width_and_signed(scope, unwrapped[1], tree)
                    if isinstance(idx_w, int) and idx_w < req_bits:
                        return (req_bits, idx_w)
    return None


def _check_target_selectors(target: object, ctx: "Context", tree: object, depth: int = 0) -> tuple[int, int] | None:
    if depth >= 64:
        return None
    if getattr(target, "is_concatenated", False):
        for elem in getattr(target, "elements", []):
            mismatch = _check_target_selectors(elem, ctx, tree, depth + 1)
            if mismatch is not None:
                return mismatch
        return None
    lhs_sels = getattr(target, "selectors", None)
    base_sym = getattr(target, "base_symbol", None)
    if lhs_sels and base_sym:
        return _check_index_selector_width_mismatch(lhs_sels, base_sym, ctx, tree)
    return None


@guarded_traversal(max_depth=64, default=None)
def _check_selects(node: object, scope: object, ctx: "Context", tree: object) -> tuple[int, int] | None:
    if node is None:
        return None
    name, selectors = extract_assignment_target_and_selectors(node)
    if name and selectors:
        lookup_hierarchical = getattr(scope, "lookup_hierarchical", None)
        sym = lookup_hierarchical(name) if callable(lookup_hierarchical) else getattr(scope, "lookup", lambda _n: None)(name)
        if sym is not None:
            mismatch = _check_index_selector_width_mismatch(selectors, sym, ctx, tree)
            if mismatch is not None:
                return mismatch
    if isinstance(node, SyntaxNode):
        for child in node:
            if isinstance(child, SyntaxNode):
                res = _check_selects(child, scope, ctx, tree)
                if res is not None:
                    return res
    return None


def _width_mismatch(vnode: BaseVNode, ctx: "Context") -> tuple[int, int] | None:
    """Return `(lhs_width, rhs_width)` when a simple assignment's recoverable
    right-hand-side width is known and differs from its target's declared
    width, else `None`.
    """
    ctx_data = getattr(ctx, "data", None)
    module_cache = ctx_data.get("module_cache") if isinstance(ctx_data, dict) else None
    cache_node = getattr(vnode, "raw", vnode)
    cached = node_cache_get(module_cache, "width_mismatch", cache_node)
    if cached is not MISSING:
        return cached  # type: ignore[return-value]

    def _store(res: tuple[int, int] | None) -> tuple[int, int] | None:
        node_cache_put(module_cache, "width_mismatch", cache_node, res)
        return res

    lhs_symbol, right = resolve_assignment_target_and_rhs(vnode, ctx)
    if lhs_symbol is None or right is None or not isinstance(lhs_symbol.bit_width, int):
        return _store(None)

    rhs_width, _rhs_signed = simple_expression_width_and_signed(ctx.scope(), right, vnode.tree)
    if not isinstance(rhs_width, int):
        return _store(None)

    intentional_extension = rhs_width < lhs_symbol.bit_width and has_explicit_signedness_cast(right)
    if lhs_symbol.bit_width != rhs_width and not intentional_extension:
        return _store((lhs_symbol.bit_width, rhs_width))

    # Check for index selector width mismatch in indexed array expressions
    scope = getattr(ctx, "scope", lambda: None)()
    if scope is not None:
        lhs_mismatch = _check_target_selectors(lhs_symbol, ctx, vnode.tree)
        if lhs_mismatch is not None:
            return _store(lhs_mismatch)

        rhs_mismatch = _check_selects(right, scope, ctx, vnode.tree)
        if rhs_mismatch is not None:
            return _store(rhs_mismatch)

    return _store(None)


def _signedness_mismatch(vnode: BaseVNode, ctx: "Context") -> tuple[bool, bool] | None:
    """Sign-mismatch sibling of `_width_mismatch`, same recoverability limits."""
    lhs_symbol, right = resolve_assignment_target_and_rhs(vnode, ctx)
    if lhs_symbol is None or right is None or lhs_symbol.is_signed is None:
        return None

    if has_explicit_signedness_cast(right):
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
    target_node_types = (BinaryExpressionNode, DeclaratorNode, ImplicitAnsiPortNode)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _width_mismatch(vnode, ctx) is not None


@rule_runner.register
class NoAssignmentSignednessMismatchRule(Rule):
    code = "ASSIGNMENT_SIGNEDNESS_MISMATCH"
    message = "Assignment right-hand side signedness does not match its target's declared signedness"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (BinaryExpressionNode, DeclaratorNode, ImplicitAnsiPortNode)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return _signedness_mismatch(vnode, ctx) is not None


@rule_runner.register
class NoAssignmentTruncationRule(Rule):
    """Narrower, direction-specific sibling of `ASSIGNMENT_WIDTH_MISMATCH`:
    fires only when the right-hand side is wider than the target, the lossy
    (data-dropping) direction of a width mismatch, as opposed to a safe
    zero/sign-extending narrower-to-wider assignment. Always co-fires with
    `ASSIGNMENT_WIDTH_MISMATCH` on the same construct -- see `overlaps_with`
    and the matching regression case in `tests/rules/overlap/test_rule_overlap_harness.py`.
    """

    code = "ASSIGNMENT_TRUNCATION"
    message = "Assignment right-hand side is wider than its target, causing implicit truncation"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    overlaps_with = ("ASSIGNMENT_WIDTH_MISMATCH",)
    target_node_types = (BinaryExpressionNode, DeclaratorNode, ImplicitAnsiPortNode)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        widths = _width_mismatch(vnode, ctx)
        return widths is not None and widths[1] > widths[0]
