from ..syntax_kinds import (
    ADD_SUBTRACT_EXPRESSION_KINDS,
    ASSIGNMENT_KINDS,
    CASEX_KEYWORD_TOKEN_KIND,
    CASEZ_KEYWORD_TOKEN_KIND,
    COMPARISON_EXPRESSION_KINDS,
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


def is_comparison_expression(raw: object) -> bool:
    """True if `raw` is a comparison expression (==, !=, <, <=, >, >=, ===, !==, ==?, !=?)."""
    return getattr(raw, "kind", None) in COMPARISON_EXPRESSION_KINDS


def comparison_operands(raw: object) -> tuple[object, object, str] | None:
    """If `raw` is a comparison expression, return `(left, right, op_text)`, else `None`."""
    if not is_comparison_expression(raw):
        return None
    left = getattr(raw, "left", None)
    right = getattr(raw, "right", None)
    op_token = getattr(raw, "operatorToken", None)
    op_text = str(op_token).strip() if op_token is not None else ""
    return left, right, op_text


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
    if style_kind == CASEX_KEYWORD_TOKEN_KIND:
        wildcard_chars = "xz?"
    elif style_kind == CASEZ_KEYWORD_TOKEN_KIND:
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


def _extract_case_pattern(expr: object, wildcards: str) -> tuple[int, str] | None:
    from .expressions import evaluate_constant_expression, unwrap_parentheses

    unwrapped = unwrap_parentheses(expr)
    kind = getattr(unwrapped, "kind", None)

    # 1. Unbased unsized literal: '0, '1, 'x, 'z
    if kind == UNBASED_UNSIZED_LITERAL_EXPRESSION_KIND:
        tok = getattr(unwrapped, "literal", None)
        if tok is not None:
            text = str(tok).strip().lstrip("'").lower()
            return 1, text

    # 2. Integer vector expression: sized/unbased vector e.g. 3'b00?, 4'hA, 2'b10
    if kind == INTEGER_VECTOR_EXPRESSION_KIND:
        val_tok = getattr(unwrapped, "value", None)
        size_tok = getattr(unwrapped, "size", None)
        base_tok = getattr(unwrapped, "base", None)
        if val_tok is not None:
            raw_text = str(val_tok).strip().replace("_", "").lower()
            base_text = str(base_tok).strip().lower() if base_tok is not None else ""
            size_int = None
            if size_tok is not None:
                try:
                    size_int = int(str(size_tok).strip())
                except ValueError:
                    pass

            if "b" in base_text:
                bit_str = raw_text
                width = size_int if size_int is not None else len(bit_str)
                if len(bit_str) < width:
                    pad_char = "0"
                    if bit_str and bit_str[0] in ("x", "z", "?"):
                        pad_char = bit_str[0]
                    bit_str = pad_char * (width - len(bit_str)) + bit_str
                return width, bit_str
            elif "o" in base_text:
                oct_to_bin = {
                    "0": "000", "1": "001", "2": "010", "3": "011",
                    "4": "100", "5": "101", "6": "110", "7": "111",
                    "x": "xxx", "z": "zzz", "?": "???"
                }
                if all(ch in oct_to_bin for ch in raw_text):
                    bit_str = "".join(oct_to_bin[ch] for ch in raw_text)
                    width = size_int if size_int is not None else len(bit_str)
                    if len(bit_str) > width:
                        bit_str = bit_str[-width:]
                    elif len(bit_str) < width:
                        pad_char = "0"
                        if bit_str and bit_str[0] in ("x", "z", "?"):
                            pad_char = bit_str[0]
                        bit_str = pad_char * (width - len(bit_str)) + bit_str
                    return width, bit_str
            elif "h" in base_text:
                hex_to_bin = {
                    "0": "0000", "1": "0001", "2": "0010", "3": "0011",
                    "4": "0100", "5": "0101", "6": "0110", "7": "0111",
                    "8": "1000", "9": "1001", "a": "1010", "b": "1011",
                    "c": "1100", "d": "1101", "e": "1110", "f": "1111",
                    "x": "xxxx", "z": "zzzz", "?": "????"
                }
                if all(ch in hex_to_bin for ch in raw_text):
                    bit_str = "".join(hex_to_bin[ch] for ch in raw_text)
                    width = size_int if size_int is not None else len(bit_str)
                    if len(bit_str) > width:
                        bit_str = bit_str[-width:]
                    elif len(bit_str) < width:
                        pad_char = "0"
                        if bit_str and bit_str[0] in ("x", "z", "?"):
                            pad_char = bit_str[0]
                        bit_str = pad_char * (width - len(bit_str)) + bit_str
                    return width, bit_str

    # 3. Standard constant integer value or evaluation
    val = constant_integer_value(unwrapped)
    if val is None:
        val = evaluate_constant_expression(unwrapped)
    if val is not None:
        if val >= 0:
            width = max(1, val.bit_length())
            return width, bin(val)[2:].zfill(width)
        else:
            uval = (1 << 32) + val
            return 32, bin(uval)[2:].zfill(32)

    return None


def _patterns_overlap(pat1: tuple[int, str], pat2: tuple[int, str], wildcards: str) -> bool:
    w1, s1 = pat1
    w2, s2 = pat2
    max_w = max(w1, w2)
    s1_ext = "0" * (max_w - w1) + s1
    s2_ext = "0" * (max_w - w2) + s2
    for b1, b2 in zip(s1_ext, s2_ext):
        if b1 in wildcards or b2 in wildcards:
            continue
        if b1 != b2:
            return False
    return True


def has_case_overlapping_items(raw: object) -> bool:
    """True if `raw` is a `CaseStatementSyntax` containing duplicate or overlapping
    case item expressions, including exact numeric duplicates (4'd2 vs 4'b0010)
    in standard `case` or wildcard overlaps (3'b00? vs 3'b001) in `casez`/`casex`."""
    from ..syntax_queries import (
        case_item_expressions,
        case_statement_items,
        is_case_statement,
    )
    from .expressions import evaluate_constant_expression, unwrap_parentheses

    if not is_case_statement(raw):
        return False

    style_kind = getattr(getattr(raw, "caseKeyword", None), "kind", None)
    if style_kind == CASEX_KEYWORD_TOKEN_KIND:
        wildcards = "xz?"
    elif style_kind == CASEZ_KEYWORD_TOKEN_KIND:
        wildcards = "z?"
    else:
        wildcards = ""

    seen_patterns: list[tuple[int, str]] = []
    seen_values: set[int] = set()

    for item in case_statement_items(raw):
        expressions = case_item_expressions(item)
        for expr in expressions:
            unwrapped = unwrap_parentheses(expr)
            # 1. Exact numeric value check for standard case (fast path)
            val = constant_integer_value(unwrapped)
            if val is None:
                val = evaluate_constant_expression(unwrapped)

            if not wildcards and val is not None:
                if val in seen_values:
                    return True
                seen_values.add(val)

            # 2. Pattern overlap check for wildcard cases or duplicate patterns
            pat = _extract_case_pattern(unwrapped, wildcards)
            if pat is not None:
                if wildcards:
                    for prev_pat in seen_patterns:
                        if _patterns_overlap(prev_pat, pat, wildcards):
                            return True
                else:
                    for prev_pat in seen_patterns:
                        if prev_pat == pat:
                            return True
                seen_patterns.append(pat)

    return False

