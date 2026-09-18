"""Expression width, signedness, and value inspection queries."""
from __future__ import annotations

from collections.abc import Mapping
import re
from typing import TYPE_CHECKING

from ..syntax_kinds import (
    ADD_EXPRESSION_KIND,
    ADD_SUBTRACT_EXPRESSION_KINDS,
    ARITHMETIC_SHIFT_LEFT_EXPRESSION_KIND,
    ARITHMETIC_SHIFT_RIGHT_EXPRESSION_KIND,
    BINARY_AND_EXPRESSION_KIND,
    BINARY_OR_EXPRESSION_KIND,
    BINARY_XOR_EXPRESSION_KIND,
    BIT_SELECT_KIND,
    CONCATENATION_EXPRESSION_KIND,
    DIVIDE_EXPRESSION_KIND,
    ELEMENT_SELECT_EXPRESSION_KIND,
    IDENTIFIER_NAME_KIND,
    IDENTIFIER_SELECT_NAME_KIND,
    INTEGER_LITERAL_EXPRESSION_KIND,
    INTEGER_VECTOR_EXPRESSION_KIND,
    INVOCATION_EXPRESSION_KIND,
    LOGICAL_SHIFT_LEFT_EXPRESSION_KIND,
    LOGICAL_SHIFT_RIGHT_EXPRESSION_KIND,
    MOD_EXPRESSION_KIND,
    MULTIPLE_CONCATENATION_EXPRESSION_KIND,
    MULTIPLY_EXPRESSION_KIND,
    PARENTHESIZED_EXPRESSION_KIND,
    POWER_EXPRESSION_KIND,
    RANGE_SELECT_KINDS,
    SHIFT_EXPRESSION_KINDS,
    SUBTRACT_EXPRESSION_KIND,
    UNARY_BITWISE_NOT_EXPRESSION_KIND,
    UNARY_MINUS_EXPRESSION_KIND,
    UNARY_PLUS_EXPRESSION_KIND,
    UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND,
)
from ..types import SyntaxNode, SyntaxTree
from .literals import constant_integer_value
from .shapes import element_select_index_or_range, identifier_name
from .shared import _split_top_level, simple_identifier_text, source_text_for_node


def unwrap_parentheses(expr: object) -> object:
    """Recursively strip `ParenthesizedExpressionSyntax`, `SimplePropertyExprSyntax`,
    and `SimpleSequenceExprSyntax` wrappers down to the underlying expression."""
    while expr is not None:
        if getattr(expr, "kind", None) == PARENTHESIZED_EXPRESSION_KIND:
            inner = getattr(expr, "expression", None)
            if inner is None:
                break
            expr = inner
        elif type(expr).__name__ in ("SimplePropertyExprSyntax", "SimpleSequenceExprSyntax"):
            inner = getattr(expr, "expr", None)
            if inner is None:
                break
            expr = inner
        else:
            break
    return expr


def _resolve_symbol_in_scope(scope: object, name: str) -> object:
    if scope is None or not name:
        return None
    if isinstance(scope, Mapping):
        if name in scope:
            val = scope[name]
            if isinstance(val, int):
                from types import SimpleNamespace
                return SimpleNamespace(value=val)
            return val
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


def evaluate_constant_expression(
    expr: object,
    scope: object = None,
    _visited: set[str] | None = None,
) -> int | None:
    """Recursively constant-fold a compile-time constant expression to an integer,
    resolving parameter/localparam identifiers against `scope`.

    Supports:
    - Sized and unsized numeric literals (decimal, hex, octal, binary)
    - Parameter and localparam symbol lookups
    - Unary operators: +, -, ~, !
    - Binary arithmetic: +, -, *, /, %
    - Exponentiation: ** (guarded up to exponent 64)
    - Shifts: <<, >>, <<<, >>> (guarded up to 128 bits)
    - Bitwise logic: &, |, ^
    - System function: $clog2(...)
    - Parentheses unwrapping
    - Cycle detection on identifier lookups to prevent infinite recursion
    """
    if expr is None:
        return None

    expr = unwrap_parentheses(expr)
    kind = getattr(expr, "kind", None)

    # 1. Simple numeric literal fast-path (also folds unary minus on literals)
    lit_val = constant_integer_value(expr)
    if lit_val is not None:
        return lit_val

    # 2. Identifier lookup in scope
    if kind == IDENTIFIER_NAME_KIND:
        name = identifier_name(expr)
        if name is not None and scope is not None:
            if _visited is None:
                _visited = set()
            if name in _visited:
                return None
            _visited.add(name)
            symbol = _resolve_symbol_in_scope(scope, name)
            if symbol is not None:
                val = getattr(symbol, "value", None)
                if isinstance(val, int):
                    return val
        return None

    # 3. Unary expressions
    if kind == UNARY_PLUS_EXPRESSION_KIND:
        op = getattr(expr, "operand", None) or getattr(expr, "expression", None)
        return evaluate_constant_expression(op, scope=scope, _visited=_visited)

    if kind == UNARY_MINUS_EXPRESSION_KIND:
        op = getattr(expr, "operand", None) or getattr(expr, "expression", None)
        val = evaluate_constant_expression(op, scope=scope, _visited=_visited)
        return -val if val is not None else None

    if kind == UNARY_BITWISE_NOT_EXPRESSION_KIND:
        op = getattr(expr, "operand", None) or getattr(expr, "expression", None)
        val = evaluate_constant_expression(op, scope=scope, _visited=_visited)
        return ~val if val is not None else None

    kind_name = type(expr).__name__
    if kind_name == "UnaryLogicalNotExpression" or getattr(kind, "name", None) == "UnaryLogicalNotExpression":
        op = getattr(expr, "operand", None) or getattr(expr, "expression", None)
        val = evaluate_constant_expression(op, scope=scope, _visited=_visited)
        return (1 if val == 0 else 0) if val is not None else None

    # 4. Invocations ($clog2)
    if kind == INVOCATION_EXPRESSION_KIND:
        left = getattr(expr, "left", None)
        tok = getattr(left, "systemIdentifier", None)
        fn_name = getattr(tok, "valueText", None) or str(left).strip()
        if fn_name == "$clog2":
            arguments = getattr(expr, "arguments", None)
            params = getattr(arguments, "parameters", None)
            if params and len(params) == 1:
                arg = params[0]
                arg_expr = getattr(arg, "expr", getattr(arg, "expression", None))
                arg_val = evaluate_constant_expression(arg_expr, scope=scope, _visited=_visited)
                if arg_val is not None:
                    return (arg_val - 1).bit_length() if arg_val > 0 else 0
        return None

    # 5. Binary expressions
    left = getattr(expr, "left", None)
    right = getattr(expr, "right", None)
    if left is not None and right is not None:
        l_val = evaluate_constant_expression(left, scope=scope, _visited=_visited)
        r_val = evaluate_constant_expression(right, scope=scope, _visited=_visited)
        if l_val is not None and r_val is not None:
            if kind == ADD_EXPRESSION_KIND:
                return l_val + r_val
            elif kind == SUBTRACT_EXPRESSION_KIND:
                return l_val - r_val
            elif kind == MULTIPLY_EXPRESSION_KIND:
                return l_val * r_val
            elif kind == DIVIDE_EXPRESSION_KIND:
                if r_val == 0:
                    return None
                return l_val // r_val
            elif kind == MOD_EXPRESSION_KIND:
                if r_val == 0:
                    return None
                return l_val % r_val
            elif kind == POWER_EXPRESSION_KIND:
                if 0 <= r_val <= 64:
                    try:
                        return l_val ** r_val
                    except (OverflowError, ValueError):
                        return None
                return None
            elif kind in (LOGICAL_SHIFT_LEFT_EXPRESSION_KIND, ARITHMETIC_SHIFT_LEFT_EXPRESSION_KIND):
                if 0 <= r_val <= 128:
                    return l_val << r_val
                return None
            elif kind in (LOGICAL_SHIFT_RIGHT_EXPRESSION_KIND, ARITHMETIC_SHIFT_RIGHT_EXPRESSION_KIND):
                if r_val >= 0:
                    return l_val >> r_val
                return None
            elif kind == BINARY_AND_EXPRESSION_KIND:
                return l_val & r_val
            elif kind == BINARY_OR_EXPRESSION_KIND:
                return l_val | r_val
            elif kind == BINARY_XOR_EXPRESSION_KIND:
                return l_val ^ r_val

    return None


def _selector_width(selector: object, scope: object = None) -> int | None:
    """Return the bit-width selected by an `ElementSelectSyntax` node."""
    unwrapped = element_select_index_or_range(selector)
    if unwrapped is None:
        return None
    shape, payload = unwrapped
    if shape == "bit":
        return 1
    if shape == "simple_range":
        left, right = payload
        l_val = evaluate_constant_expression(left, scope=scope)
        r_val = evaluate_constant_expression(right, scope=scope)
        if l_val is not None and r_val is not None:
            return abs(l_val - r_val) + 1
        return None
    if shape in ("ascending", "descending"):
        _base, width_expr = payload
        return evaluate_constant_expression(width_expr, scope=scope)
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
                width = _selector_width(valid_selectors[-1], scope=scope)
                return width, None
        return None, None

    if kind == ELEMENT_SELECT_EXPRESSION_KIND:
        select = getattr(expr, "select", None)
        if select is not None:
            width = _selector_width(select, scope=scope)
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
        count = evaluate_constant_expression(count_node, scope=scope)
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


def evaluate_constant_text_expression(expr_text: str | None, scope: object = None) -> int | None:
    """Parse an expression text string into a native pyslang CST/AST node and
    constant-fold it against `scope`. Encapsulates pyslang syntax tree construction."""
    if not expr_text or not expr_text.strip():
        return None
    try:
        import pyslang as sl
        tree = sl.SyntaxTree.fromText(expr_text.strip())
        if tree is None or tree.root is None:
            return None
        return evaluate_constant_expression(tree.root, scope=scope)
    except Exception:
        return None


def evaluate_packed_dimension_bounds(
    dimension_texts: list[tuple[str, str]],
    scope: object = None,
) -> tuple[int | None, int | None, int | None]:
    """Evaluate packed dimension text pairs [(msb_text, lsb_text), ...] against `scope`.
    Returns (total_bit_width, first_msb, first_lsb) where total_bit_width is the
    product of all folded dimension widths. If any dimension fails to fold, returns (None, None, None)."""
    if not dimension_texts:
        return None, None, None
    total_width = 1
    first_msb: int | None = None
    first_lsb: int | None = None
    for index, (msb_text, lsb_text) in enumerate(dimension_texts):
        msb_val = evaluate_constant_text_expression(msb_text, scope=scope)
        lsb_val = evaluate_constant_text_expression(lsb_text, scope=scope)
        if msb_val is None or lsb_val is None:
            return None, None, None
        if index == 0:
            first_msb = msb_val
            first_lsb = lsb_val
        dim_width = abs(msb_val - lsb_val) + 1
        total_width *= dim_width
    return total_width, first_msb, first_lsb

