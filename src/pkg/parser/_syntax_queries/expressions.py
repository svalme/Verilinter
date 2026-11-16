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
    CAST_EXPRESSION_KIND,
    DOUBLE_COLON_TOKEN_KIND,
    INTEGER_TYPE_KINDS,
    SIGNED_CAST_EXPRESSION_KIND,
    BITWISE_BINARY_EXPRESSION_KINDS,
    CONCATENATION_EXPRESSION_KIND,
    CONTEXT_DETERMINED_EXPRESSION_KINDS,
    CONDITIONAL_EXPRESSION_KIND,
    DIVIDE_EXPRESSION_KIND,
    ELEMENT_SELECT_EXPRESSION_KIND,
    IDENTIFIER_NAME_KIND,
    IDENTIFIER_SELECT_NAME_KIND,
    SCOPED_NAME_KIND,
    INTEGER_LITERAL_EXPRESSION_KIND,
    INTEGER_VECTOR_EXPRESSION_KIND,
    INVOCATION_EXPRESSION_KIND,
    LOGICAL_AND_EXPRESSION_KIND,
    LOGICAL_OR_EXPRESSION_KIND,
    LOGICAL_SHIFT_LEFT_EXPRESSION_KIND,
    LOGICAL_SHIFT_RIGHT_EXPRESSION_KIND,
    MOD_EXPRESSION_KIND,
    MULTIPLE_CONCATENATION_EXPRESSION_KIND,
    MULTIPLY_EXPRESSION_KIND,
    ONE_BIT_RESULT_EXPRESSION_KINDS,
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
from ..traversal_guard import guarded_traversal
from ..types import SyntaxNode, SyntaxTree
from .literals import (
    UNSIZED_DECIMAL_LITERAL_WIDTH,
    constant_integer_value,
    is_unsized_literal,
    literal_width_and_signed,
)
from .shapes import element_select_index_or_range
from .shared import identifier_name


_EVALUATABLE_BINARY_KINDS = (
    ADD_EXPRESSION_KIND,
    SUBTRACT_EXPRESSION_KIND,
    MULTIPLY_EXPRESSION_KIND,
    DIVIDE_EXPRESSION_KIND,
    MOD_EXPRESSION_KIND,
    POWER_EXPRESSION_KIND,
    LOGICAL_SHIFT_LEFT_EXPRESSION_KIND,
    ARITHMETIC_SHIFT_LEFT_EXPRESSION_KIND,
    LOGICAL_SHIFT_RIGHT_EXPRESSION_KIND,
    ARITHMETIC_SHIFT_RIGHT_EXPRESSION_KIND,
    BINARY_AND_EXPRESSION_KIND,
    BINARY_OR_EXPRESSION_KIND,
    BINARY_XOR_EXPRESSION_KIND,
    EQUALITY_EXPRESSION_KIND,
    CASE_EQUALITY_EXPRESSION_KIND,
    WILDCARD_EQUALITY_EXPRESSION_KIND,
    INEQUALITY_EXPRESSION_KIND,
    CASE_INEQUALITY_EXPRESSION_KIND,
    WILDCARD_INEQUALITY_EXPRESSION_KIND,
    LESS_THAN_EXPRESSION_KIND,
    LESS_THAN_EQUAL_EXPRESSION_KIND,
    GREATER_THAN_EXPRESSION_KIND,
    GREATER_THAN_EQUAL_EXPRESSION_KIND,
    LOGICAL_AND_EXPRESSION_KIND,
    LOGICAL_OR_EXPRESSION_KIND,
)


def is_context_determined_expression(expr: object) -> bool:
    """True when the outermost operator takes its operand width from the context it is used in.

    An expression such as `a + b` assigned or connected to a wider target is evaluated at the target's
    width, so its own estimated width being smaller than the target's is not a mismatch.
    """
    return getattr(unwrap_parentheses(expr), "kind", None) in CONTEXT_DETERMINED_EXPRESSION_KINDS


def is_width_bounded_operand(expr: object) -> bool:
    """True for a name, select or concatenation: a value limited to its declared width.

    An arithmetic result such as `a + b` is evaluated at the context width, so it can exceed the
    width its operands suggest and is not bounded in this sense.
    """
    kind = getattr(unwrap_parentheses(expr), "kind", None)
    return kind in (
        IDENTIFIER_NAME_KIND,
        IDENTIFIER_SELECT_NAME_KIND,
        SCOPED_NAME_KIND,
        ELEMENT_SELECT_EXPRESSION_KIND,
        CONCATENATION_EXPRESSION_KIND,
    )


def unwrap_parentheses(expr: object) -> object:
    """Recursively strip `ParenthesizedExpressionSyntax`, `SimplePropertyExprSyntax`,
    and `SimpleSequenceExprSyntax` wrappers down to the underlying expression."""
    depth = 0
    seen: set[int] = set()
    while expr is not None and depth < 64:
        eid = id(expr)
        if eid in seen:
            break
        seen.add(eid)
        depth += 1
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


def _is_constant_symbol_operand(scope: object, expr: object) -> bool:
    """True for a name that resolves to a parameter, localparam or enum member."""
    symbol = _resolve_symbol_in_scope(scope, identifier_name(unwrap_parentheses(expr)) or "")
    return bool(getattr(symbol, "is_compile_time_constant", False))


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
    depth = 0
    seen: set[int] = set()
    while current is not None and depth < 64:
        cid = id(current)
        if cid in seen:
            break
        seen.add(cid)
        depth += 1
        symbol = getattr(current, "lookup", lambda _name: None)(name)
        if symbol is not None:
            return symbol
        current = getattr(current, "parent", None)
    return None


def _extract_predicate_expression(predicate: object) -> object:
    if predicate is None:
        return None
    conditions = getattr(predicate, "conditions", None)
    if conditions:
        try:
            first = conditions[0]
            expr = getattr(first, "expr", None) or getattr(first, "expression", None)
            if expr is not None:
                return expr
            return first
        except (IndexError, TypeError):
            pass
    expr = getattr(predicate, "expr", None) or getattr(predicate, "expression", None)
    if expr is not None:
        return expr
    return predicate


@guarded_traversal(max_depth=64, default=None)
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
    - Conditional (ternary) operator: ? :
    - Parentheses unwrapping
    - Cycle detection on identifier lookups and AST nodes to prevent infinite recursion
    - Iterative flattening of associative binary spines and ternary cascades in O(1) recursion depth
    """
    if expr is None or not isinstance(expr, SyntaxNode):
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

    # 2b. A package-qualified name (`pkg::NAME`): the package's own constant.
    if kind == SCOPED_NAME_KIND and getattr(getattr(expr, "separator", None), "kind", None) == DOUBLE_COLON_TOKEN_KIND:
        package_name = identifier_name(getattr(expr, "left", None))
        member_name = identifier_name(getattr(expr, "right", None))
        lookup = getattr(scope, "lookup_package_member", None)
        if package_name and member_name and callable(lookup):
            symbol = lookup(package_name, member_name)
            value = getattr(symbol, "value", None)
            if isinstance(value, int):
                return value
        return None

    # Type casts that keep the value: `unsigned'(x)`, `signed'(x)` and `int'(x)` of a small constant.
    # A size cast (`8'(x)`) or a named type can change the value, so those are left unknown.
    if kind == SIGNED_CAST_EXPRESSION_KIND:
        return evaluate_constant_expression(getattr(expr, "inner", None), scope=scope, _visited=_visited)
    if kind == CAST_EXPRESSION_KIND and getattr(getattr(expr, "left", None), "kind", None) in INTEGER_TYPE_KINDS:
        return evaluate_constant_expression(getattr(expr, "right", None), scope=scope, _visited=_visited)

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

    # 5. Conditional (ternary) expression: iteratively walk false-branch spine in O(1) recursion depth
    if kind == CONDITIONAL_EXPRESSION_KIND:
        curr = expr
        depth_iter = 0
        seen_ternary: set[int] = set()
        while getattr(curr, "kind", None) == CONDITIONAL_EXPRESSION_KIND and depth_iter < 1024:
            cid = id(curr)
            if cid in seen_ternary:
                return None
            seen_ternary.add(cid)
            depth_iter += 1

            cond_raw = getattr(curr, "predicate", None) or getattr(curr, "condition", None)
            cond_expr = _extract_predicate_expression(cond_raw)
            cond_val = evaluate_constant_expression(cond_expr, scope=scope, _visited=_visited)
            if cond_val is None:
                return None
            if cond_val != 0:
                true_expr = getattr(curr, "left", None)
                return evaluate_constant_expression(true_expr, scope=scope, _visited=_visited)
            curr = unwrap_parentheses(getattr(curr, "right", None))

        return evaluate_constant_expression(curr, scope=scope, _visited=_visited)

    # 6. Associative binary expressions: iteratively unwind left spines in O(1) recursion depth
    if kind in (
        ADD_EXPRESSION_KIND,
        SUBTRACT_EXPRESSION_KIND,
        MULTIPLY_EXPRESSION_KIND,
        BINARY_AND_EXPRESSION_KIND,
        BINARY_OR_EXPRESSION_KIND,
        BINARY_XOR_EXPRESSION_KIND,
    ):
        operands = []
        curr = expr
        depth_iter = 0
        seen_spine: set[int] = set()
        while getattr(curr, "kind", None) == kind and depth_iter < 1024:
            cid = id(curr)
            if cid in seen_spine:
                return None
            seen_spine.add(cid)
            depth_iter += 1
            operands.append(getattr(curr, "right", None))
            curr = unwrap_parentheses(getattr(curr, "left", None))
        operands.append(curr)
        operands.reverse()

        if kind == ADD_EXPRESSION_KIND:
            total = 0
            for op in operands:
                val = evaluate_constant_expression(op, scope=scope, _visited=_visited)
                if val is None:
                    return None
                total += val
            return total

        if kind == SUBTRACT_EXPRESSION_KIND:
            first = True
            total = 0
            for op in operands:
                val = evaluate_constant_expression(op, scope=scope, _visited=_visited)
                if val is None:
                    return None
                if first:
                    total = val
                    first = False
                else:
                    total -= val
            return total

        if kind == MULTIPLY_EXPRESSION_KIND:
            total = 1
            for op in operands:
                val = evaluate_constant_expression(op, scope=scope, _visited=_visited)
                if val is None:
                    return None
                total *= val
            return total

        if kind == BINARY_AND_EXPRESSION_KIND:
            first = True
            total = 0
            for op in operands:
                val = evaluate_constant_expression(op, scope=scope, _visited=_visited)
                if val is None:
                    return None
                if first:
                    total = val
                    first = False
                else:
                    total &= val
            return total

        if kind == BINARY_OR_EXPRESSION_KIND:
            total = 0
            for op in operands:
                val = evaluate_constant_expression(op, scope=scope, _visited=_visited)
                if val is None:
                    return None
                total |= val
            return total

        if kind == BINARY_XOR_EXPRESSION_KIND:
            total = 0
            for op in operands:
                val = evaluate_constant_expression(op, scope=scope, _visited=_visited)
                if val is None:
                    return None
                total ^= val
            return total

    # 7. Non-associative binary expressions (divide, mod, power, shifts, comparisons, logical)
    if kind in _EVALUATABLE_BINARY_KINDS:
        left = getattr(expr, "left", None)
        right = getattr(expr, "right", None)
        if left is not None and right is not None:
            l_val = evaluate_constant_expression(left, scope=scope, _visited=_visited)
            r_val = evaluate_constant_expression(right, scope=scope, _visited=_visited)
            if l_val is not None and r_val is not None:
                if kind == DIVIDE_EXPRESSION_KIND:
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
                elif kind == LOGICAL_AND_EXPRESSION_KIND:
                    return int(bool(l_val) and bool(r_val))
                elif kind == LOGICAL_OR_EXPRESSION_KIND:
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

        packed_widths = list(getattr(symbol, "packed_dimension_widths", []))
        if not packed_widths and getattr(symbol, "packed_dimensions", None):
            for msb_txt, lsb_txt in symbol.packed_dimensions:
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
                    packed_widths.append(abs(m - l) + 1)
                else:
                    packed_widths.append(None)

        # If symbol has a known bit width and no explicit packed dimensions (e.g. 1-bit logic or multi-bit integer),
        # treat its packed element width as [symbol.bit_width] when unpacked dimensions exist.
        if unpacked_widths and not packed_widths and isinstance(getattr(symbol, "bit_width", None), int):
            packed_widths = [symbol.bit_width]

        # An element of a named type has the width of that type, which is not known here, and the
        # dimensions written after the type name are not recorded.
        named_dimensions = getattr(symbol, "named_type_dimension_count", None)
        if named_dimensions:
            return None
        if named_dimensions == 0:
            packed_widths = [*packed_widths, None]

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
            symbol = _resolve_symbol_in_scope(scope, name)
            if symbol is not None:
                return getattr(symbol, "bit_width", None), getattr(symbol, "is_signed", None)
        return None, None

    cast = _signedness_cast(expr)
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


def is_sign_neutral_expression(expr: object) -> bool:
    """True when the signedness of `expr` cannot change what it means: an unsized decimal literal, which is
    signed by the language but reads the same value in a signed or an unsigned context. Signedness-mismatch
    rules ask this before comparing signedness, so each of them need not decide it again. A shift takes
    its signedness from the shifted operand, so `1 << n` is neutral too."""
    for _ in range(32):
        expr = unwrap_parentheses(expr)
        if getattr(expr, "kind", None) not in SHIFT_EXPRESSION_KINDS:
            return is_unsized_literal(expr)
        expr = getattr(expr, "left", None)
    return False


def _signedness_cast(expr: object) -> tuple[object, bool] | None:
    """Recognize the two width-preserving system casts structurally."""
    if getattr(expr, "kind", None) != INVOCATION_EXPRESSION_KIND:
        return None
    token = getattr(getattr(expr, "left", None), "systemIdentifier", None)
    name = getattr(token, "valueText", None)
    if name not in ("$signed", "$unsigned"):
        return None
    parameters = getattr(getattr(expr, "arguments", None), "parameters", ())
    if len(parameters) != 1:
        return None
    argument = getattr(parameters[0], "expr", None)
    return (argument, name == "$signed") if isinstance(argument, SyntaxNode) else None


def has_explicit_signedness_cast(expr: object) -> bool:
    """Whether a cast explicitly sets result signedness, including a shift LHS."""
    for _ in range(32):
        expr = unwrap_parentheses(expr)
        if _signedness_cast(expr) is not None:
            return True
        if getattr(expr, "kind", None) not in SHIFT_EXPRESSION_KINDS:
            return False
        expr = getattr(expr, "left", None)
    return False


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
        if _is_constant_symbol_operand(scope, getattr(expr, "left", None)) or _is_constant_symbol_operand(
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
