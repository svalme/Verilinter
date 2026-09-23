"""Expression width, signedness, and value inspection queries."""
from __future__ import annotations

from collections.abc import Mapping
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
    SIMPLE_PROPERTY_EXPR_KIND,
    SIMPLE_SEQUENCE_EXPR_KIND,
    SUBTRACT_EXPRESSION_KIND,
    UNARY_BITWISE_NOT_EXPRESSION_KIND,
    UNARY_LOGICAL_NOT_EXPRESSION_KIND,
    UNARY_MINUS_EXPRESSION_KIND,
    UNARY_PLUS_EXPRESSION_KIND,
    UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND,
    CASE_EQUALITY_EXPRESSION_KIND,
    CASE_INEQUALITY_EXPRESSION_KIND,
    EQUALITY_EXPRESSION_KIND,
    GREATER_THAN_EQUAL_EXPRESSION_KIND,
    GREATER_THAN_EXPRESSION_KIND,
    INEQUALITY_EXPRESSION_KIND,
    LESS_THAN_EQUAL_EXPRESSION_KIND,
    LESS_THAN_EXPRESSION_KIND,
    WILDCARD_EQUALITY_EXPRESSION_KIND,
    WILDCARD_INEQUALITY_EXPRESSION_KIND,
)
from ..types import SyntaxNode, SyntaxTree
from .literals import constant_integer_value
from .shapes import element_select_index_or_range
from .shared import identifier_name


def unwrap_parentheses(expr: object) -> object:
    """Recursively strip `ParenthesizedExpressionSyntax`, `SimplePropertyExprSyntax`,
    and `SimpleSequenceExprSyntax` wrappers down to the underlying expression."""
    while expr is not None:
        kind = getattr(expr, "kind", None)
        if kind == PARENTHESIZED_EXPRESSION_KIND:
            inner = getattr(expr, "expression", None)
            if inner is None:
                break
            expr = inner
        elif kind in (SIMPLE_PROPERTY_EXPR_KIND, SIMPLE_SEQUENCE_EXPR_KIND):
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

    if kind == UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND:
        tok = getattr(expr, "literal", None)
        if tok is not None:
            text = str(tok).strip().lstrip("'").lower()
            if text == "0":
                return 0
            elif text == "1":
                return 1

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

    if kind == UNARY_LOGICAL_NOT_EXPRESSION_KIND:
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
            elif kind in (EQUALITY_EXPRESSION_KIND, CASE_EQUALITY_EXPRESSION_KIND, WILDCARD_EQUALITY_EXPRESSION_KIND):
                return int(l_val == r_val)
            elif kind in (INEQUALITY_EXPRESSION_KIND, CASE_INEQUALITY_EXPRESSION_KIND, WILDCARD_INEQUALITY_EXPRESSION_KIND):
                return int(l_val != r_val)
            elif kind == LESS_THAN_EXPRESSION_KIND:
                return int(l_val < r_val)
            elif kind == LESS_THAN_EQUAL_EXPRESSION_KIND:
                return int(l_val <= r_val)
            elif kind == GREATER_THAN_EXPRESSION_KIND:
                return int(l_val > r_val)
            elif kind == GREATER_THAN_EQUAL_EXPRESSION_KIND:
                return int(l_val >= r_val)
            else:
                kind_name = getattr(kind, "name", str(kind))
                if kind_name == "LogicalAndExpression":
                    return int(bool(l_val) and bool(r_val))
                elif kind_name == "LogicalOrExpression":
                    return int(bool(l_val) or bool(r_val))

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


def compute_sliced_width(
    symbol: object | None,
    selectors: list[object],
    scope: object = None,
) -> int | None:
    """Compute the bit width resulting from indexing or slicing an identifier with `selectors`.

    Supports:
    - Single-element bit selects on 1D vectors (`vec[i]` -> 1 bit)
    - Element selects on multi-dimensional packed arrays (`arr[i]` -> element slice width)
    - Nested element selects (`arr[i][j]` -> scalar bit width or sub-slice width)
    - Simple range selects (`vec[7:0]` -> 8 bits, `arr[3:1]` -> range count * inner element width)
    - Indexed part-selects (`vec[i +: 8]` -> 8 bits)
    """
    if not selectors:
        return getattr(symbol, "bit_width", None) if symbol is not None else None

    # Recover individual unpacked and packed dimension widths
    unpacked_widths: list[int | None] = []
    packed_widths: list[int | None] = []
    if symbol is not None:
        unpacked_widths = list(getattr(symbol, "unpacked_dimension_widths", []))
        if not unpacked_widths and getattr(symbol, "unpacked_dimensions", None):
            for msb_txt, lsb_txt in symbol.unpacked_dimensions:
                try:
                    m = int(msb_txt)
                    l = int(lsb_txt)
                    unpacked_widths.append(abs(m - l) + 1)
                except (ValueError, TypeError):
                    unpacked_widths.append(None)

        packed_widths = list(getattr(symbol, "packed_dimension_widths", []))
        if not packed_widths and getattr(symbol, "packed_dimensions", None):
            for msb_txt, lsb_txt in symbol.packed_dimensions:
                try:
                    m = int(msb_txt)
                    l = int(lsb_txt)
                    packed_widths.append(abs(m - l) + 1)
                except (ValueError, TypeError):
                    packed_widths.append(None)

        # If symbol has a known bit width and no explicit packed dimensions (e.g. 1-bit logic or multi-bit integer),
        # treat its packed element width as [symbol.bit_width] when unpacked dimensions exist.
        if unpacked_widths and not packed_widths and isinstance(getattr(symbol, "bit_width", None), int):
            packed_widths = [symbol.bit_width]

    num_unpacked = len(unpacked_widths)

    # Compute single packed element bit width (product of all packed dimensions)
    packed_elem_width: int | None = None
    if packed_widths:
        if any(d is None for d in packed_widths):
            packed_elem_width = None
        else:
            prod = 1
            for d in packed_widths:
                prod *= d
            packed_elem_width = prod
    elif symbol is not None and isinstance(getattr(symbol, "bit_width", None), int):
        packed_elem_width = symbol.bit_width
    elif not unpacked_widths:
        packed_elem_width = None
    else:
        packed_elem_width = 1

    slice_width: int | None = None

    for s_idx, selector in enumerate(selectors):
        unwrapped = element_select_index_or_range(selector)
        if unwrapped is None:
            return None
        shape, payload = unwrapped
        is_last = (s_idx == len(selectors) - 1)

        if s_idx < num_unpacked:
            # Indexing or slicing an unpacked array dimension
            if shape == "bit":
                if is_last:
                    rem_unpacked = unpacked_widths[s_idx + 1:]
                    if any(d is None for d in rem_unpacked) or packed_elem_width is None:
                        slice_width = None
                    else:
                        prod = packed_elem_width
                        for d in rem_unpacked:
                            prod *= d
                        slice_width = prod
            elif shape == "simple_range":
                left, right = payload
                l_val = evaluate_constant_expression(left, scope=scope)
                r_val = evaluate_constant_expression(right, scope=scope)
                if l_val is None or r_val is None:
                    return None
                range_count = abs(l_val - r_val) + 1
                if is_last:
                    rem_unpacked = unpacked_widths[s_idx + 1:]
                    if any(d is None for d in rem_unpacked) or packed_elem_width is None:
                        slice_width = None
                    else:
                        prod = range_count * packed_elem_width
                        for d in rem_unpacked:
                            prod *= d
                        slice_width = prod
            elif shape in ("ascending", "descending"):
                _base, width_expr = payload
                w_val = evaluate_constant_expression(width_expr, scope=scope)
                if w_val is None:
                    return None
                if is_last:
                    rem_unpacked = unpacked_widths[s_idx + 1:]
                    if any(d is None for d in rem_unpacked) or packed_elem_width is None:
                        slice_width = None
                    else:
                        prod = w_val * packed_elem_width
                        for d in rem_unpacked:
                            prod *= d
                        slice_width = prod
        else:
            # Indexing or slicing packed dimensions
            p_idx = s_idx - num_unpacked

            if shape == "bit":
                if is_last:
                    rem_dims = packed_widths[p_idx + 1:] if packed_widths else []
                    if not rem_dims:
                        slice_width = 1
                    elif any(d is None for d in rem_dims):
                        slice_width = None
                    else:
                        prod = 1
                        for d in rem_dims:
                            prod *= d
                        slice_width = prod

            elif shape == "simple_range":
                left, right = payload
                l_val = evaluate_constant_expression(left, scope=scope)
                r_val = evaluate_constant_expression(right, scope=scope)
                if l_val is None or r_val is None:
                    return None
                range_count = abs(l_val - r_val) + 1
                if is_last:
                    rem_dims = packed_widths[p_idx + 1:] if packed_widths else []
                    if not rem_dims:
                        slice_width = range_count
                    elif any(d is None for d in rem_dims):
                        slice_width = None
                    else:
                        prod = range_count
                        for d in rem_dims:
                            prod *= d
                        slice_width = prod

            elif shape in ("ascending", "descending"):
                _base, width_expr = payload
                w_val = evaluate_constant_expression(width_expr, scope=scope)
                if w_val is None:
                    return None
                if is_last:
                    rem_dims = packed_widths[p_idx + 1:] if packed_widths else []
                    if not rem_dims:
                        slice_width = w_val
                    elif any(d is None for d in rem_dims):
                        slice_width = None
                    else:
                        prod = w_val
                        for d in rem_dims:
                            prod *= d
                        slice_width = prod

    return slice_width



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
        name = identifier_name(expr)
        selectors = getattr(expr, "selectors", None)
        symbol = _resolve_symbol_in_scope(scope, name) if (name and scope) else None
        if selectors:
            valid_selectors = [s for s in selectors if isinstance(s, SyntaxNode)]
            if valid_selectors:
                width = compute_sliced_width(symbol, valid_selectors, scope=scope)
                return width, None
        return None, None

    if kind == ELEMENT_SELECT_EXPRESSION_KIND:
        nested_selectors: list[SyntaxNode] = []
        curr = expr
        while getattr(curr, "kind", None) == ELEMENT_SELECT_EXPRESSION_KIND:
            sel = getattr(curr, "select", None)
            if isinstance(sel, SyntaxNode):
                nested_selectors.append(sel)
            curr = getattr(curr, "left", None)
        base_name = identifier_name(curr)
        symbol = _resolve_symbol_in_scope(scope, base_name) if (base_name and scope) else None
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
            if getattr(concat_node, "kind", None) == INTEGER_LITERAL_EXPRESSION_KIND:
                inner_width = 32
            else:
                inner_width, _ = simple_expression_width_and_signed(scope, concat_node, tree)
            if inner_width is not None:
                return count * inner_width, False
        return None, None

    if kind in SHIFT_EXPRESSION_KINDS:
        left = getattr(expr, "left", None)
        if left is not None:
            return simple_expression_width_and_signed(scope, left, tree)
        return None, None

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


def evaluate_constant_text_expression(expr_text: str | None, scope: object = None) -> int | None:
    """Parse an expression text string into a native CST/AST node and
    constant-fold it against `scope`. Encapsulates syntax tree construction."""
    if not expr_text or not expr_text.strip():
        return None
    try:
        from ..parse import parse_text

        tree = parse_text(expr_text.strip())
        if tree is None or getattr(tree, "root", None) is None:
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

