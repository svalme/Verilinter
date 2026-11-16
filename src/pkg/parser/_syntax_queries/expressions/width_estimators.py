"""Expression width and signedness: the simple, operand and natural estimators (`EXPRESSION_TYPE_MODEL_DESIGN.md` 2.1)."""
from __future__ import annotations

from ...syntax_kinds import (
    ADD_SUBTRACT_EXPRESSION_KINDS,
    BITWISE_BINARY_EXPRESSION_KINDS,
    CONCATENATION_EXPRESSION_KIND,
    CONDITIONAL_EXPRESSION_KIND,
    ELEMENT_SELECT_EXPRESSION_KIND,
    IDENTIFIER_NAME_KIND,
    IDENTIFIER_SELECT_NAME_KIND,
    MULTIPLE_CONCATENATION_EXPRESSION_KIND,
    MULTIPLY_EXPRESSION_KIND,
    ONE_BIT_RESULT_EXPRESSION_KINDS,
    SHIFT_EXPRESSION_KINDS,
    UNARY_BITWISE_NOT_EXPRESSION_KIND,
)
from ...traversal_guard import guarded_traversal
from ...types import SyntaxNode, SyntaxTree
from ..literals import UNSIZED_DECIMAL_LITERAL_WIDTH, is_unsized_literal, literal_width_and_signed
from ..shared import identifier_name
from .operand_shapes import unwrap_parentheses, signedness_cast
from .symbol_resolution import resolve_symbol_in_scope, is_constant_symbol_operand
from .constant_evaluation import evaluate_constant_expression
from .select_widths import compute_sliced_width


@guarded_traversal(node_arg="expr", max_depth=64, default=(None, None))
def simple_expression_width_and_signed(
    scope: object,
    expr: SyntaxNode,
    tree: SyntaxTree | None = None,
) -> tuple[int | None, bool | None]:
    """Recover the declared or literal bit width and signedness of a simple
    expression -- an identifier, a sized or unsized literal, a bit- or
    part-select, a concatenation or replication of those, or a shift whose
    natural width is determined by its shifted operand.

    Returns `(width, is_signed)` with each element `int | None` and
    `bool | None`. An unsized decimal literal (`5`) returns `(None, False)`
    so a rule like `ASSIGNMENT_WIDTH_MISMATCH` knows it has no recoverable
    declared width, except when used as a concatenation member where IEEE 1800
    fixes its width at 32 bits.

    Complex binary expressions (`+`, `-`, `*`) are intentionally excluded here
    so assignment rules do not conflate assignment mismatch with arithmetic
    overflow/truncation; see `natural_expression_width_and_signed` for the
    self-determined arithmetic evaluator.
    """
    if not isinstance(expr, SyntaxNode):
        return None, None

    expr = unwrap_parentheses(expr)
    kind = getattr(expr, "kind", None)

    if kind == IDENTIFIER_NAME_KIND:
        name = identifier_name(expr)
        if name is not None:
            symbol = resolve_symbol_in_scope(scope, name)
            if symbol is not None:
                # A bare unpacked array is the whole object, not one element.
                whole_width = getattr(symbol, "whole_width", None)
                width = whole_width if isinstance(whole_width, int) else getattr(symbol, "bit_width", None)
                return width, getattr(symbol, "is_signed", None)
        return None, None

    cast = signedness_cast(expr)
    if cast is not None:
        argument, signed = cast
        width, _ = expression_width_and_signed(scope, argument, tree)
        return width, signed if width is not None else None

    if kind == CONDITIONAL_EXPRESSION_KIND:
        branches = []
        curr = expr
        depth_iter = 0
        seen_ternary: set[int] = set()
        while getattr(curr, "kind", None) == CONDITIONAL_EXPRESSION_KIND and depth_iter < 1024:
            cid = id(curr)
            if cid in seen_ternary:
                return None, None
            seen_ternary.add(cid)
            depth_iter += 1
            branches.append(getattr(curr, "left", None))
            curr = unwrap_parentheses(getattr(curr, "right", None))
        branches.append(curr)

        max_width: int | None = None
        all_signed: bool | None = True
        for branch in branches:
            if branch is None:
                return None, None
            b_width, b_signed = expression_width_and_signed(scope, branch, tree)
            if b_width is None:
                return None, None
            max_width = b_width if max_width is None else max(max_width, b_width)
            if b_signed is None:
                all_signed = None
            elif all_signed is not None and not b_signed:
                all_signed = False
        return max_width, all_signed

    literal_type = literal_width_and_signed(expr)
    if literal_type is not None:
        return literal_type

    if kind == IDENTIFIER_SELECT_NAME_KIND:
        name = identifier_name(expr)
        selectors = getattr(expr, "selectors", None)
        symbol = resolve_symbol_in_scope(scope, name) if (name and scope) else None
        if selectors:
            valid_selectors = [s for s in selectors if isinstance(s, SyntaxNode)]
            if valid_selectors:
                width = compute_sliced_width(symbol, valid_selectors, scope=scope)
                return width, None
        return None, None

    if kind == ELEMENT_SELECT_EXPRESSION_KIND:
        nested_selectors: list[SyntaxNode] = []
        curr = expr
        depth = 0
        seen_curr: set[int] = set()
        while getattr(curr, "kind", None) == ELEMENT_SELECT_EXPRESSION_KIND and depth < 64:
            cid = id(curr)
            if cid in seen_curr:
                break
            seen_curr.add(cid)
            depth += 1
            sel = getattr(curr, "select", None)
            if isinstance(sel, SyntaxNode):
                nested_selectors.append(sel)
            curr = getattr(curr, "left", None)
        base_name = identifier_name(curr)
        symbol = resolve_symbol_in_scope(scope, base_name) if (base_name and scope) else None
        ordered_selectors = list(reversed(nested_selectors))
        width = compute_sliced_width(symbol, ordered_selectors, scope=scope)
        return width, None

    if kind == CONCATENATION_EXPRESSION_KIND:
        raw_expressions = getattr(expr, "expressions", None)
        if raw_expressions is not None:
            members = [e for e in raw_expressions if isinstance(e, SyntaxNode)]
            if not members:
                return None, None
            total = 0
            for member in members:
                unwrapped_member = unwrap_parentheses(member)
                if is_unsized_literal(unwrapped_member):
                    total += UNSIZED_DECIMAL_LITERAL_WIDTH
                else:
                    m_width, _ = simple_expression_width_and_signed(
                        scope, unwrapped_member, tree
                    )
                    if m_width is None:
                        return None, None
                    total += m_width
            return total, False
        return None, None

    if kind == MULTIPLE_CONCATENATION_EXPRESSION_KIND:
        count_node = unwrap_parentheses(getattr(expr, "expression", None))
        concat_node = unwrap_parentheses(getattr(expr, "concatenation", None))
        count = evaluate_constant_expression(count_node, scope=scope)
        if count is not None and concat_node is not None:
            if is_unsized_literal(concat_node):
                inner_width = UNSIZED_DECIMAL_LITERAL_WIDTH
            else:
                inner_width, _ = simple_expression_width_and_signed(
                    scope, concat_node, tree
                )
            if inner_width is not None:
                return count * inner_width, False
        return None, None

    if kind in SHIFT_EXPRESSION_KINDS:
        left = getattr(expr, "left", None)
        if left is not None:
            return simple_expression_width_and_signed(scope, left, tree)
        return None, None

    return None, None


@guarded_traversal(max_depth=64, default=(None, None), node_arg="expr")
def expression_width_and_signed(scope: object, expr: SyntaxNode, tree: SyntaxTree | None = None) -> tuple[int | None, bool | None]:
    """Language operand width before assignment context, without bit growth.

    Arithmetic uses max operand width, including multiplication. The separate
    natural query estimates full-product capacity for the truncation policy.
    """
    expr = unwrap_parentheses(expr)
    target_kinds = (*ADD_SUBTRACT_EXPRESSION_KINDS, MULTIPLY_EXPRESSION_KIND)
    if getattr(expr, "kind", None) in target_kinds:
        operands = []
        curr = expr
        depth_iter = 0
        seen_spine: set[int] = set()
        while getattr(curr, "kind", None) in target_kinds and depth_iter < 1024:
            cid = id(curr)
            if cid in seen_spine:
                return None, None
            seen_spine.add(cid)
            depth_iter += 1
            operands.append(getattr(curr, "right", None))
            curr = unwrap_parentheses(getattr(curr, "left", None))
        operands.append(curr)

        max_width: int | None = None
        all_signed: bool | None = True
        for op in operands:
            if op is None:
                return None, None
            op_width, op_signed = expression_width_and_signed(scope, op, tree)
            if op_width is None:
                return None, None
            max_width = op_width if max_width is None else max(max_width, op_width)
            if op_signed is None:
                all_signed = None
            elif all_signed is not None and not op_signed:
                all_signed = False
        return max_width, all_signed
    return simple_expression_width_and_signed(scope, expr, tree)


@guarded_traversal(max_depth=128, default=(None, None), node_arg="expr")
def natural_expression_width_and_signed(
    scope: object,
    expr: SyntaxNode,
    tree: SyntaxTree | None = None,
) -> tuple[int | None, bool | None]:
    """Estimate arithmetic capacity recursively, not an IEEE expression type.

    This policy query extends simple operand typing with:
    - Add/subtract: `max(left_width, right_width)`.
    - Multiply: full-product capacity `left_width + right_width`.
    - Signedness: signed only when both operands are known signed.
    - Comparison, logical and reduction operators: one unsigned bit.
    - Bitwise operators: the widest operand (`~x`: the width of `x`).
    Casts form self-determined boundaries and addition carry-out is excluded.
    """
    if not isinstance(expr, SyntaxNode):
        return None, None

    expr = unwrap_parentheses(expr)
    kind = getattr(expr, "kind", None)

    if kind in ADD_SUBTRACT_EXPRESSION_KINDS:
        operands = []
        curr = expr
        depth_iter = 0
        seen_spine: set[int] = set()
        while getattr(curr, "kind", None) in ADD_SUBTRACT_EXPRESSION_KINDS and depth_iter < 1024:
            cid = id(curr)
            if cid in seen_spine:
                return None, None
            seen_spine.add(cid)
            depth_iter += 1
            operands.append(getattr(curr, "right", None))
            curr = unwrap_parentheses(getattr(curr, "left", None))
        operands.append(curr)

        max_width: int | None = None
        all_signed: bool | None = True
        for op in operands:
            if op is None:
                return None, None
            op_w, op_s = natural_expression_width_and_signed(scope, op, tree)
            if not isinstance(op_w, int):
                return None, None
            max_width = op_w if max_width is None else max(max_width, op_w)
            if op_s is None:
                all_signed = None
            elif all_signed is not None and not op_s:
                all_signed = False
        return max_width, all_signed

    if kind == MULTIPLY_EXPRESSION_KIND:
        operands = []
        curr = expr
        depth_iter = 0
        seen_spine: set[int] = set()
        while getattr(curr, "kind", None) == MULTIPLY_EXPRESSION_KIND and depth_iter < 1024:
            cid = id(curr)
            if cid in seen_spine:
                return None, None
            seen_spine.add(cid)
            depth_iter += 1
            operands.append(getattr(curr, "right", None))
            curr = unwrap_parentheses(getattr(curr, "left", None))
        operands.append(curr)

        total_width: int = 0
        all_signed: bool | None = True
        for op in operands:
            if op is None:
                return None, None
            op_w, op_s = natural_expression_width_and_signed(scope, op, tree)
            if not isinstance(op_w, int):
                return None, None
            total_width += op_w
            if op_s is None:
                all_signed = None
            elif all_signed is not None and not op_s:
                all_signed = False
        return total_width, all_signed

    if kind == CONDITIONAL_EXPRESSION_KIND:
        branches = []
        curr = expr
        depth_iter = 0
        seen_ternary: set[int] = set()
        while getattr(curr, "kind", None) == CONDITIONAL_EXPRESSION_KIND and depth_iter < 1024:
            cid = id(curr)
            if cid in seen_ternary:
                return None, None
            seen_ternary.add(cid)
            depth_iter += 1
            branches.append(getattr(curr, "left", None))
            curr = unwrap_parentheses(getattr(curr, "right", None))
        branches.append(curr)

        max_width: int | None = None
        all_signed: bool | None = True
        for branch in branches:
            if branch is None:
                return None, None
            b_width, b_signed = natural_expression_width_and_signed(scope, branch, tree)
            if not isinstance(b_width, int):
                return None, None
            max_width = b_width if max_width is None else max(max_width, b_width)
            if b_signed is None:
                all_signed = None
            elif all_signed is not None and not b_signed:
                all_signed = False
        return max_width, all_signed

    # A bitwise operator is as wide as its widest operand; `~x` is as wide as `x`. A parameter operand adapts
    # to the other operand and to the target (`localparam integer` is 32 bits wide but holds a small value),
    # so its declared width is not the width of the result.
    if kind in BITWISE_BINARY_EXPRESSION_KINDS:
        if is_constant_symbol_operand(scope, getattr(expr, "left", None)) or is_constant_symbol_operand(
            scope, getattr(expr, "right", None)
        ):
            return None, None
        left_width, left_signed = natural_expression_width_and_signed(scope, getattr(expr, "left", None), tree)
        right_width, right_signed = natural_expression_width_and_signed(scope, getattr(expr, "right", None), tree)
        if not isinstance(left_width, int) or not isinstance(right_width, int):
            return None, None
        if left_signed is None or right_signed is None:
            return max(left_width, right_width), None
        return max(left_width, right_width), left_signed and right_signed
    if kind == UNARY_BITWISE_NOT_EXPRESSION_KIND:
        return natural_expression_width_and_signed(scope, getattr(expr, "operand", None), tree)

    # Comparisons, logical operators and reductions yield one unsigned bit whatever their operand widths.
    if kind in ONE_BIT_RESULT_EXPRESSION_KINDS:
        return 1, False

    # A cast is a self-determined boundary: do not propagate a hypothetical
    # full product width through it.
    return simple_expression_width_and_signed(scope, expr, tree)
