"""What an expression node is, without evaluating it: unwrapping parentheses, the operators whose width the context decides, width-bounded operands, and signedness casts."""
from __future__ import annotations

from ...syntax_kinds import (
    CONCATENATION_EXPRESSION_KIND,
    CONTEXT_DETERMINED_EXPRESSION_KINDS,
    ELEMENT_SELECT_EXPRESSION_KIND,
    IDENTIFIER_NAME_KIND,
    IDENTIFIER_SELECT_NAME_KIND,
    SCOPED_NAME_KIND,
    INVOCATION_EXPRESSION_KIND,
    PARENTHESIZED_EXPRESSION_KIND,
    SHIFT_EXPRESSION_KINDS,
    SIMPLE_PROPERTY_EXPR_KIND,
    SIMPLE_SEQUENCE_EXPR_KIND,
)
from ...types import SyntaxNode
from ..literals import is_unsized_literal


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


def is_context_determined_expression(expr: object) -> bool:
    """True when the outermost operator is `+`, `-`, `*` or a left shift.

    Such a result can need more bits than its operands, and its operands are evaluated at the width of the
    target, so a target wider than the estimated operand width is sized on purpose and is not a mismatch.
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


def signedness_cast(expr: object) -> tuple[object, bool] | None:
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
        if signedness_cast(expr) is not None:
            return True
        if getattr(expr, "kind", None) not in SHIFT_EXPRESSION_KINDS:
            return False
        expr = getattr(expr, "left", None)
    return False
