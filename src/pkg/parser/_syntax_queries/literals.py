import pyslang as sl

from ..syntax_kinds import (
    ADD_SUBTRACT_EXPRESSION_KINDS,
    ASSIGNMENT_KINDS,
    CONDITIONAL_EXPRESSION_KIND,
    CONTINUOUS_ASSIGN_KIND,
    DIVIDE_EXPRESSION_KIND,
    EQUALITY_EXPRESSION_KIND,
    FOR_LOOP_STATEMENT_KIND,
    INEQUALITY_EXPRESSION_KIND,
    INTEGER_LITERAL_EXPRESSION_KIND,
    INTEGER_VECTOR_EXPRESSION_KIND,
    MOD_EXPRESSION_KIND,
    MULTIPLY_EXPRESSION_KIND,
    PROCEDURAL_BLOCK_KINDS,
    READ_WRITE_ASSIGNMENT_KINDS,
    READ_WRITE_UNARY_KINDS,
    SHIFT_EXPRESSION_KINDS,
    SIMPLE_ASSIGNMENT_KINDS,
    UNARY_MINUS_EXPRESSION_KIND,
    UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND,
)
from ..types import IDENTIFIER_NAME_NODE_TYPES, ProceduralBlockNode


def is_assignment_expression(raw: object) -> bool:
    return getattr(raw, "kind", None) in ASSIGNMENT_KINDS


def is_read_write_assignment_expression(raw: object) -> bool:
    return getattr(raw, "kind", None) in READ_WRITE_ASSIGNMENT_KINDS


def is_read_write_unary_expression(raw: object) -> bool:
    return getattr(raw, "kind", None) in READ_WRITE_UNARY_KINDS


def is_procedural_block(raw: object) -> bool:
    return isinstance(raw, ProceduralBlockNode) or getattr(raw, "kind", None) in PROCEDURAL_BLOCK_KINDS


def is_identifier_name_node(raw: object) -> bool:
    return isinstance(raw, IDENTIFIER_NAME_NODE_TYPES)


def is_continuous_assign(raw: object) -> bool:
    return getattr(raw, "kind", None) == CONTINUOUS_ASSIGN_KIND


def is_unsized_literal(raw: object) -> bool:
    return getattr(raw, "kind", None) == INTEGER_LITERAL_EXPRESSION_KIND


def is_unsized_literal_in_flagged_value_context(raw: object) -> bool:
    """True if `raw` is a plain, unsized, unbased decimal literal (`5`, not
    `8'd5`/`'hFF`/`'0` -- those are different SyntaxKinds entirely) that is the
    direct right-hand side of a blocking (`=`) or non-blocking (`<=`) assignment.
    A continuous `assign x = 5;` shares the identical AssignmentExpression node
    shape, so this one check covers both procedural and continuous assignment.

    Excludes a classic `for (i = 0; ...; i = i + 1)` loop header: its init/step
    clauses are ordinary AssignmentExpression/NonblockingAssignmentExpression
    nodes parented directly by ForLoopStatementSyntax, the same shape as an
    ordinary assignment statement. A `generate for` header needs no such
    exclusion -- LoopGenerateSyntax models its init/step via dedicated fields,
    never as a nested assignment expression, so it never reaches this check.
    """
    if not is_unsized_literal(raw):
        return False
    assignment = getattr(raw, "parent", None)
    if getattr(assignment, "kind", None) not in SIMPLE_ASSIGNMENT_KINDS:
        return False
    if getattr(assignment, "right", None) is not raw:
        return False
    if getattr(getattr(assignment, "parent", None), "kind", None) == FOR_LOOP_STATEMENT_KIND:
        return False
    return True


def sized_literal_overflow(raw: object) -> tuple[int, int] | None:
    """Return `(declared_width, minimum_required_width)` if `raw` is a
    fully-numeric (no `x`/`z`/`?`), unsigned sized literal (`4'hFF`) whose
    value needs more bits than its declared width, else `None`.

    First pass only covers unsigned literals -- a signed sized literal's
    (`4'shF`) two's-complement minimum-width math is a separate, more careful
    calculation not attempted here.
    """
    if getattr(raw, "kind", None) != INTEGER_VECTOR_EXPRESSION_KIND:
        return None

    size_token = getattr(raw, "size", None)
    base_token = getattr(raw, "base", None)
    value_token = getattr(raw, "value", None)
    if size_token is None or base_token is None or value_token is None:
        return None

    size_text = str(size_token).strip()
    base_text = str(base_token).strip().lstrip("'")
    value_text = str(value_token).strip().replace("_", "")
    if not size_text.isdigit() or not base_text:
        return None
    declared_width = int(size_text)

    if base_text[:1].lower() == "s":
        return None
    radix = {"b": 2, "o": 8, "d": 10, "h": 16}.get(base_text[-1:].lower())
    if radix is None or any(ch in "xz?" for ch in value_text.lower()):
        return None

    try:
        numeric_value = int(value_text, radix)
    except ValueError:
        return None

    minimum_width = max(numeric_value.bit_length(), 1)
    if minimum_width > declared_width:
        return declared_width, minimum_width
    return None


def _xz_literal_bit_text(raw: object) -> str | None:
    """Return the lowercase literal-value text for `raw` if it is an
    unbased-unsized literal (`'x`) or a sized vector literal (`4'bx01z`),
    else `None`. Shared text-extraction step for `is_explicit_xz_literal` and
    `has_casex_casez_wildcard_case_item`.
    """
    kind = getattr(raw, "kind", None)
    if kind == UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND:
        literal_token = getattr(raw, "literal", None)
        if literal_token is None:
            return None
        return str(literal_token).strip().lstrip("'").lower()
    if kind == INTEGER_VECTOR_EXPRESSION_KIND:
        value_token = getattr(raw, "value", None)
        if value_token is None:
            return None
        return str(value_token).strip().replace("_", "").lower()
    return None


def is_explicit_xz_literal(raw: object) -> bool:
    """True if `raw` is an unbased-unsized `'x`/`'z` literal, or a sized
    literal (`4'bx01z`) whose value contains an explicit x/z/? bit -- a value
    that can never occur on real synthesized hardware and defeats
    reset/comparison determinism if written directly into RTL as a value.
    """
    text = _xz_literal_bit_text(raw)
    if text is None:
        return False
    if getattr(raw, "kind", None) == UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND:
        return text in ("x", "z")
    return any(ch in "xz?" for ch in text)


def is_xz_equality_comparison(raw: object) -> bool:
    """True if `raw` is a plain `==`/`!=` (EqualityExpression/InequalityExpression
    -- distinct SyntaxKinds from case-equality `===`/`!==` and wildcard-equality
    `==?`/`!=?`) comparing against an explicit X/Z literal on either side.
    """
    if getattr(raw, "kind", None) not in (EQUALITY_EXPRESSION_KIND, INEQUALITY_EXPRESSION_KIND):
        return False
    left = getattr(raw, "left", None)
    right = getattr(raw, "right", None)
    return is_explicit_xz_literal(left) or is_explicit_xz_literal(right)


def _is_all_wildcard_text(raw: object, wildcard_chars: str) -> bool:
    text = _xz_literal_bit_text(raw)
    return bool(text) and all(ch in wildcard_chars for ch in text)


def has_casex_casez_wildcard_case_item(raw: object) -> bool:
    """True if `raw` is a `casex`/`casez` CaseStatementSyntax containing a case
    item whose every expression is composed entirely of that case style's
    wildcard characters -- `x`/`z`/`?` for `casex`, but only `z`/`?` for
    `casez` (`x` is not a wildcard there) -- meaning the item silently matches
    every possible value.
    """
    from ..syntax_queries import case_item_expressions, case_statement_items, is_case_statement

    if not is_case_statement(raw):
        return False

    style_kind = getattr(getattr(raw, "caseKeyword", None), "kind", None)
    if style_kind == sl.TokenKind.CaseXKeyword:
        wildcard_chars = "xz?"
    elif style_kind == sl.TokenKind.CaseZKeyword:
        wildcard_chars = "z?"
    else:
        return False

    for item in case_statement_items(raw):
        expressions = case_item_expressions(item)
        if expressions and all(_is_all_wildcard_text(expression, wildcard_chars) for expression in expressions):
            return True
    return False


def is_shift_expression(raw: object) -> bool:
    return getattr(raw, "kind", None) in SHIFT_EXPRESSION_KINDS


def is_divide_or_mod_expression(raw: object) -> bool:
    return getattr(raw, "kind", None) in (DIVIDE_EXPRESSION_KIND, MOD_EXPRESSION_KIND)


def is_add_subtract_expression(raw: object) -> bool:
    return getattr(raw, "kind", None) in ADD_SUBTRACT_EXPRESSION_KINDS


def is_multiply_expression(raw: object) -> bool:
    return getattr(raw, "kind", None) == MULTIPLY_EXPRESSION_KIND


def _unsigned_literal_integer_value(raw: object) -> int | None:
    """Return the numeric value of a plain unsized decimal literal or a
    fully-numeric unsigned sized literal, else `None`. Shared constant-folding
    step for `constant_integer_value`; a signed sized literal (`4'shF`) is
    skipped, the same conservative scope `sized_literal_overflow` uses."""
    if getattr(raw, "kind", None) == INTEGER_LITERAL_EXPRESSION_KIND:
        literal_token = getattr(raw, "literal", None)
        text = str(literal_token).strip().replace("_", "") if literal_token is not None else ""
        return int(text) if text.isdigit() else None

    if getattr(raw, "kind", None) == INTEGER_VECTOR_EXPRESSION_KIND:
        base_token = getattr(raw, "base", None)
        value_token = getattr(raw, "value", None)
        if base_token is None or value_token is None:
            return None
        base_text = str(base_token).strip().lstrip("'")
        value_text = str(value_token).strip().replace("_", "")
        if not base_text or base_text[:1].lower() == "s":
            return None
        radix = {"b": 2, "o": 8, "d": 10, "h": 16}.get(base_text[-1:].lower())
        if radix is None or any(ch in "xz?" for ch in value_text.lower()):
            return None
        try:
            return int(value_text, radix)
        except ValueError:
            return None

    return None


def constant_integer_value(raw: object) -> int | None:
    """Best-effort constant-fold a simple literal expression -- a plain
    unsized decimal, a fully-numeric unsigned sized literal, or a unary minus
    wrapping either -- to a Python `int`, else `None`. Deliberately narrow:
    variables, richer expressions, and any x/z/?-valued literal are not
    folded -- the shared "is this operand a compile-time constant we can
    reason about" primitive for `SHIFT_AMOUNT_OUT_OF_RANGE`,
    `DIVISION_BY_ZERO_CONSTANT`, and `CONSTANT_INDEX_OUT_OF_RANGE`.
    """
    if getattr(raw, "kind", None) == UNARY_MINUS_EXPRESSION_KIND:
        operand = getattr(raw, "operand", None)
        value = _unsigned_literal_integer_value(operand)
        return -value if value is not None else None

    return _unsigned_literal_integer_value(raw)


def is_tristate_continuous_assign(raw: object) -> bool:
    """True if `raw` (a ContinuousAssignSyntax, the same node
    `enclosing_continuous_assign`/`is_continuous_assign` return/check) contains
    a sub-assignment whose right-hand side is a ternary with a fully
    high-impedance (`z`-only) branch -- the classic tri-state driver-enable
    pattern (`assign bus = enable ? value : 'bz;`, or the reversed form).
    """
    assignments = getattr(raw, "assignments", None)
    if not assignments:
        return False

    for assignment in assignments:
        rhs = getattr(assignment, "right", None)
        if getattr(rhs, "kind", None) != CONDITIONAL_EXPRESSION_KIND:
            continue
        left = getattr(rhs, "left", None)
        right = getattr(rhs, "right", None)
        if _is_all_wildcard_text(left, "z") or _is_all_wildcard_text(right, "z"):
            return True
    return False
