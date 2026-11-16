"""Folding an expression to an integer: the constant evaluator, its text form, and the bounds of packed dimensions."""
from __future__ import annotations

from ...syntax_kinds import (
    ADD_EXPRESSION_KIND,
    ARITHMETIC_SHIFT_LEFT_EXPRESSION_KIND,
    ARITHMETIC_SHIFT_RIGHT_EXPRESSION_KIND,
    BINARY_AND_EXPRESSION_KIND,
    BINARY_OR_EXPRESSION_KIND,
    BINARY_XOR_EXPRESSION_KIND,
    CAST_EXPRESSION_KIND,
    DOUBLE_COLON_TOKEN_KIND,
    INTEGER_TYPE_KINDS,
    SIGNED_CAST_EXPRESSION_KIND,
    CONDITIONAL_EXPRESSION_KIND,
    DIVIDE_EXPRESSION_KIND,
    IDENTIFIER_NAME_KIND,
    IDENTIFIER_SELECT_NAME_KIND,
    SCOPED_NAME_KIND,
    INVOCATION_EXPRESSION_KIND,
    LOGICAL_AND_EXPRESSION_KIND,
    LOGICAL_OR_EXPRESSION_KIND,
    LOGICAL_SHIFT_LEFT_EXPRESSION_KIND,
    LOGICAL_SHIFT_RIGHT_EXPRESSION_KIND,
    MOD_EXPRESSION_KIND,
    MULTIPLY_EXPRESSION_KIND,
    POWER_EXPRESSION_KIND,
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
from ...traversal_guard import guarded_traversal
from ...types import SyntaxNode
from ..literals import constant_integer_value
from ..shared import identifier_name
from .operand_shapes import unwrap_parentheses
from .member_selects import member_select_width_and_signed
from .symbol_resolution import resolve_package_member_in_scope, resolve_symbol_in_scope


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


def _declared_bits(argument: object, scope: object) -> int | None:
    """`$bits` of a typedef or a declared variable (`$bits(status_t)`, `$bits(bus.addr)`), when its width is known."""
    argument = unwrap_parentheses(argument)
    kind = getattr(argument, "kind", None)
    if kind == SCOPED_NAME_KIND:
        width, _signed = member_select_width_and_signed(scope, argument)
        return width
    name = identifier_name(argument) if kind in (IDENTIFIER_NAME_KIND, IDENTIFIER_SELECT_NAME_KIND) else None
    symbol = resolve_symbol_in_scope(scope, name) if name else None
    whole_width = getattr(symbol, "whole_width", None)
    return whole_width if isinstance(whole_width, int) else None


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
            symbol = resolve_symbol_in_scope(scope, name)
            if symbol is not None:
                val = getattr(symbol, "value", None)
                if isinstance(val, int):
                    return val
        return None

    # 2b. A package-qualified name (`pkg::NAME`): the package's own constant.
    if kind == SCOPED_NAME_KIND and getattr(getattr(expr, "separator", None), "kind", None) == DOUBLE_COLON_TOKEN_KIND:
        package_name = identifier_name(getattr(expr, "left", None))
        member_name = identifier_name(getattr(expr, "right", None))
        if package_name and member_name:
            symbol = resolve_package_member_in_scope(scope, package_name, member_name)
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
        if fn_name == "$bits":
            params = getattr(getattr(expr, "arguments", None), "parameters", None)
            if params and len(params) == 1:
                return _declared_bits(getattr(params[0], "expr", getattr(params[0], "expression", None)), scope)
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


def evaluate_constant_text_expression(expr_text: str | None, scope: object = None) -> int | None:
    """Parse an expression text string into a native CST/AST node and
    constant-fold it against `scope`. Encapsulates syntax tree construction."""
    if not expr_text or not expr_text.strip():
        return None
    try:
        from ...parse import parse_text

        tree = parse_text(expr_text.strip())
        if tree is None or getattr(tree, "root", None) is None:
            return None
        return evaluate_constant_expression(tree.root, scope=scope)
    except Exception:
        return None


def constant_text_identifiers(expr_text: str | None) -> frozenset[str]:
    """The names an expression text refers to, for telling whether it depends on a given parameter."""
    if not expr_text or not expr_text.strip():
        return frozenset()
    try:
        from ...parse import parse_text
        from ..procedural.blocks import iter_identifier_nodes

        tree = parse_text(expr_text.strip())
        if tree is None or getattr(tree, "root", None) is None:
            return frozenset()
        return frozenset(name for name, _node in iter_identifier_nodes(tree.root))
    except Exception:
        return frozenset()


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
