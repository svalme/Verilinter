"""Expression width, signedness, and value inspection queries."""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..syntax_kinds import (
    ADD_SUBTRACT_EXPRESSION_KINDS,
    BIT_SELECT_KIND,
    CONCATENATION_EXPRESSION_KIND,
    ELEMENT_SELECT_EXPRESSION_KIND,
    IDENTIFIER_NAME_KIND,
    IDENTIFIER_SELECT_NAME_KIND,
    INTEGER_LITERAL_EXPRESSION_KIND,
    INTEGER_VECTOR_EXPRESSION_KIND,
    MULTIPLE_CONCATENATION_EXPRESSION_KIND,
    MULTIPLY_EXPRESSION_KIND,
    PARENTHESIZED_EXPRESSION_KIND,
    RANGE_SELECT_KINDS,
    SHIFT_EXPRESSION_KINDS,
    UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND,
)
from ..types import SyntaxNode, SyntaxTree
from .literals import constant_integer_value
from .shapes import element_select_index_or_range, identifier_name
from .shared import _split_top_level, simple_identifier_text, source_text_for_node


def unwrap_parentheses(expr: object) -> object:
    """Recursively strip `ParenthesizedExpressionSyntax` wrappers down to the
    underlying expression."""
    while getattr(expr, "kind", None) == PARENTHESIZED_EXPRESSION_KIND:
        inner = getattr(expr, "expression", None)
        if inner is None:
            break
        expr = inner
    return expr


def _resolve_symbol_in_scope(scope: object, name: str) -> object:
    if scope is None or not name:
        return None
    lookup_hierarchical = getattr(scope, "lookup_hierarchical", None)
    if callable(lookup_hierarchical):
        return lookup_hierarchical(name)
    current = scope
    while current is not None:
        symbol = getattr(current, "lookup", lambda _name: None)(name)
        if symbol is not None:
            return symbol
        current = getattr(current, "parent", None)
    return None


def _selector_width(selector: object) -> int | None:
    """Return the bit-width selected by an `ElementSelectSyntax` node."""
    unwrapped = element_select_index_or_range(selector)
    if unwrapped is None:
        return None
    shape, payload = unwrapped
    if shape == "bit":
        return 1
    if shape == "simple_range":
        left, right = payload
        l_val = constant_integer_value(left)
        r_val = constant_integer_value(right)
        if l_val is not None and r_val is not None:
            return abs(l_val - r_val) + 1
        return None
    if shape in ("ascending", "descending"):
        _base, width_expr = payload
        return constant_integer_value(width_expr)
    return None


def simple_expression_width_and_signed(
    scope: object, expr: SyntaxNode, tree: SyntaxTree | None = None
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
    expr = unwrap_parentheses(expr)
    kind = getattr(expr, "kind", None)

    if kind == IDENTIFIER_NAME_KIND:
        name = identifier_name(expr)
        if name is not None:
            symbol = _resolve_symbol_in_scope(scope, name)
            if symbol is not None:
                return getattr(symbol, "bit_width", None), getattr(symbol, "is_signed", None)
        return None, None

    if kind == INTEGER_VECTOR_EXPRESSION_KIND:
        size_node = getattr(expr, "size", None)
        size_val = getattr(size_node, "value", None)
        base_node = getattr(expr, "base", None)
        base_text = str(getattr(base_node, "rawText", base_node) or "").lower()
        if size_val is not None:
            try:
                size = int(size_val)
                return size, "'s" in base_text
            except (ValueError, TypeError):
                pass
        return None, "'s" in base_text

    if kind in (INTEGER_LITERAL_EXPRESSION_KIND, UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND):
        return None, False

    if kind == IDENTIFIER_SELECT_NAME_KIND:
        selectors = getattr(expr, "selectors", None)
        if selectors:
            valid_selectors = [s for s in selectors if isinstance(s, SyntaxNode)]
            if valid_selectors:
                width = _selector_width(valid_selectors[-1])
                return width, None
        return None, None

    if kind == ELEMENT_SELECT_EXPRESSION_KIND:
        select = getattr(expr, "select", None)
        if select is not None:
            width = _selector_width(select)
            return width, None
        return None, None

    if kind == CONCATENATION_EXPRESSION_KIND:
        raw_expressions = getattr(expr, "expressions", None)
        if raw_expressions is not None:
            members = [e for e in raw_expressions if isinstance(e, SyntaxNode)]
            if not members:
                return None, None
            total = 0
            for member in members:
                unwrapped_member = unwrap_parentheses(member)
                if getattr(unwrapped_member, "kind", None) == INTEGER_LITERAL_EXPRESSION_KIND:
                    total += 32
                else:
                    m_width, _ = simple_expression_width_and_signed(scope, unwrapped_member, tree)
                    if m_width is None:
                        return None, None
                    total += m_width
            return total, False
        return None, None

    if kind == MULTIPLE_CONCATENATION_EXPRESSION_KIND:
        count_node = unwrap_parentheses(getattr(expr, "expression", None))
        concat_node = unwrap_parentheses(getattr(expr, "concatenation", None))
        count = constant_integer_value(count_node)
        if count is not None and concat_node is not None:
            inner_width, _ = simple_expression_width_and_signed(scope, concat_node, tree)
            if inner_width is not None:
                return count * inner_width, False
        return None, None

    if kind in SHIFT_EXPRESSION_KINDS:
        left = getattr(expr, "left", None)
        if left is not None:
            return simple_expression_width_and_signed(scope, left, tree)
        return None, None

    # Fallback to source-text inference if AST shape was unrecognized or tree is provided
    if tree is not None:
        expr_text = source_text_for_node(expr, tree)
        if expr_text is not None:
            return _infer_text_width_and_signed_direct(scope, expr_text)

    return None, None


def natural_expression_width_and_signed(
    scope: object, expr: SyntaxNode, tree: SyntaxTree | None = None
) -> tuple[int | None, bool | None]:
    """Return the natural (self-determined) result width and signedness of
    `expr`, extending `simple_expression_width_and_signed` to cover binary
    arithmetic expressions (`+`, `-`, `*`).

    Per IEEE 1364/1800:
    - Add/subtract: `max(left_width, right_width)`.
    - Multiply: `left_width + right_width`.
    - Signedness: signed only when both operands are signed.
    """
    expr = unwrap_parentheses(expr)
    kind = getattr(expr, "kind", None)

    if kind in ADD_SUBTRACT_EXPRESSION_KINDS:
        left = getattr(expr, "left", None)
        right = getattr(expr, "right", None)
        if left is not None and right is not None:
            l_w, l_s = simple_expression_width_and_signed(scope, left, tree)
            r_w, r_s = simple_expression_width_and_signed(scope, right, tree)
            if isinstance(l_w, int) and isinstance(r_w, int):
                return max(l_w, r_w), bool(l_s and r_s)
        return None, None

    if kind == MULTIPLY_EXPRESSION_KIND:
        left = getattr(expr, "left", None)
        right = getattr(expr, "right", None)
        if left is not None and right is not None:
            l_w, l_s = simple_expression_width_and_signed(scope, left, tree)
            r_w, r_s = simple_expression_width_and_signed(scope, right, tree)
            if isinstance(l_w, int) and isinstance(r_w, int):
                return l_w + r_w, bool(l_s and r_s)
        return None, None

    return simple_expression_width_and_signed(scope, expr, tree)


def _concatenation_member_width(scope: object, member_text: str) -> int | None:
    width, _signed = _infer_text_width_and_signed_direct(scope, member_text)
    if width is None and re.match(r"\s*\d+\s*$", member_text):
        return 32
    return width


def _infer_text_width_and_signed_direct(scope: object, expr_text: str) -> tuple[int | None, bool | None]:
    simple_identifier = simple_identifier_text(expr_text)
    if simple_identifier is not None and scope is not None:
        symbol = _resolve_symbol_in_scope(scope, simple_identifier)
        if symbol is not None:
            return getattr(symbol, "bit_width", None), getattr(symbol, "is_signed", None)

    sized_literal = re.match(r"(?i)\s*(\d+)\s*'\s*[sS]?[bodhBODH][0-9a-f_xz?]+\s*$", expr_text)
    if sized_literal is not None:
        return int(sized_literal.group(1)), "'s" in expr_text.lower()

    unsized_decimal = re.match(r"\s*\d+\s*$", expr_text)
    if unsized_decimal is not None:
        return None, False

    bit_select = re.match(r"^(?P<base>[a-zA-Z_][a-zA-Z0-9_$]*)\s*\[\s*[^:\[\]]+\s*\]$", expr_text)
    if bit_select is not None:
        return 1, None

    part_select = re.match(
        r"^(?P<base>[a-zA-Z_][a-zA-Z0-9_$]*)\s*\[\s*(?P<left>-?\d+)\s*:\s*(?P<right>-?\d+)\s*\]$",
        expr_text,
    )
    if part_select is not None:
        return abs(int(part_select.group("left")) - int(part_select.group("right"))) + 1, None

    indexed_part_select = re.match(
        r"^(?P<base>[a-zA-Z_][a-zA-Z0-9_$]*)\s*\[\s*.+?\s*[+-]:\s*(?P<width>\d+)\s*\]$",
        expr_text,
    )
    if indexed_part_select is not None:
        return int(indexed_part_select.group("width")), None

    if expr_text.startswith("{") and expr_text.endswith("}"):
        inner = expr_text[1:-1].strip()
        replication = re.match(r"^(?P<count>\d+)\s*\{(?P<body>.*)\}$", inner)
        if replication is not None:
            inner_width = _concatenation_member_width(scope, replication.group("body"))
            if inner_width is None:
                return None, None
            return int(replication.group("count")) * inner_width, None

        parts = _split_top_level(inner, ",")
        if not parts:
            return None, None
        total = 0
        for part in parts:
            width = _concatenation_member_width(scope, part)
            if width is None:
                return None, None
            total += width
        return total, None

    shift_match = re.match(r"^(?P<left>.+?)\s*(?:<<|>>|<<<|>>>)\s*(?P<right>.+?)$", expr_text)
    if shift_match is not None:
        left_text = shift_match.group("left").strip()
        while left_text.startswith("(") and left_text.endswith(")"):
            left_text = left_text[1:-1].strip()
        return _infer_text_width_and_signed_direct(scope, left_text)

    return None, None
