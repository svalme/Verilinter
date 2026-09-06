import re

from ..syntax_kinds import (
    ALWAYS_COMB_BLOCK_KIND,
    PRIMITIVE_INSTANTIATION_KIND,
)
from ..types import SyntaxNode
from .shared import _split_top_level, simple_identifier_text, source_text_for_node


def contains_descendant(root: SyntaxNode, target: SyntaxNode) -> bool:
    if root is target:
        return True
    for child in root:
        if isinstance(child, SyntaxNode) and contains_descendant(child, target):
            return True
    return False


def assignment_left(raw: object) -> SyntaxNode | None:
    from ..syntax_queries import is_assignment_expression

    if not is_assignment_expression(raw):
        return None
    left = getattr(raw, "left", None)
    return left if isinstance(left, SyntaxNode) else None


def binary_operands(raw: object) -> tuple[SyntaxNode, SyntaxNode] | None:
    """Return `(left, right)` for any binary-expression-shaped node -- shift,
    divide, and mod expressions all share this plain `.left`/`.right` shape --
    else `None`."""
    left = getattr(raw, "left", None)
    right = getattr(raw, "right", None)
    if isinstance(left, SyntaxNode) and isinstance(right, SyntaxNode):
        return left, right
    return None


def unary_write_operand(raw: object) -> SyntaxNode | None:
    from ..syntax_queries import is_read_write_unary_expression

    if not is_read_write_unary_expression(raw):
        return None
    operand = getattr(raw, "operand", None)
    return operand if isinstance(operand, SyntaxNode) else None


def _selectors_containing_identifier(raw: object, raw_identifier: SyntaxNode) -> bool:
    selectors = getattr(raw, "selectors", None)
    if selectors is None:
        return False

    for selector in selectors:
        if isinstance(selector, SyntaxNode) and contains_descendant(selector, raw_identifier):
            return True
    return False


def _identifier_access_modes_over_ancestors(
    raw_ancestors: list[object], raw_identifier: SyntaxNode
) -> tuple[bool, bool]:
    from ..syntax_queries import is_read_write_assignment_expression

    for ancestor in reversed(raw_ancestors):
        left = assignment_left(ancestor)
        if left is not None and contains_descendant(left, raw_identifier):
            if _selectors_containing_identifier(left, raw_identifier):
                return True, False
            if is_read_write_assignment_expression(ancestor):
                return True, True
            return False, True

        operand = unary_write_operand(ancestor)
        if operand is not None and contains_descendant(operand, raw_identifier):
            return True, True

    return True, False


def identifier_access_modes(ctx: "Context", raw_identifier: SyntaxNode) -> tuple[bool, bool]:
    return _identifier_access_modes_over_ancestors([a.raw for a in ctx.stack], raw_identifier)


def enclosing_procedural_block(ctx: "Context") -> "BaseVNode | None":
    from ..syntax_queries import is_procedural_block

    for ancestor in reversed(ctx.stack):
        if is_procedural_block(ancestor.raw):
            return ancestor
    return None


def enclosing_primitive_instantiation(ctx: "Context") -> "BaseVNode | None":
    for ancestor in reversed(ctx.stack):
        if getattr(ancestor.raw, "kind", None) == PRIMITIVE_INSTANTIATION_KIND:
            return ancestor
    return None


def enclosing_continuous_assign(ctx: "Context") -> "BaseVNode | None":
    from ..syntax_queries import is_continuous_assign

    for ancestor in reversed(ctx.stack):
        if is_continuous_assign(ancestor.raw):
            return ancestor
    return None


def is_combinational_driver_block(driver_block: "BaseVNode") -> bool:
    from ..syntax_queries import is_combinational_style_always_block, is_continuous_assign

    raw = driver_block.raw
    return (
        is_continuous_assign(raw)
        or getattr(raw, "kind", None) == ALWAYS_COMB_BLOCK_KIND
        or is_combinational_style_always_block(raw)
    )


def enclosing_case_statement(ctx: "Context") -> "BaseVNode | None":
    from ..syntax_queries import is_case_statement

    for ancestor in reversed(ctx.stack):
        if is_case_statement(ancestor.raw):
            return ancestor
    return None


def _conditional_references_any_name(raw: object, names: set[str]) -> bool:
    from .procedural import _iter_identifier_nodes

    predicate = getattr(raw, "predicate", None)
    conditions = getattr(predicate, "conditions", None) or []
    for condition in conditions:
        expr = getattr(condition, "expr", None)
        if expr is None:
            continue
        for name, _identifier in _iter_identifier_nodes(expr):
            if name in names:
                return True
    return False


def is_within_async_reset_conditional(ctx: "Context") -> bool:
    """True if the current traversal position is inside a conditional whose
    predicate references one of the enclosing procedural block's async-reset
    sensitivity-list signals -- e.g. inside the `if (rst)`/`else` of
    `always @(posedge clk or posedge rst) if (rst) ...`. Used by
    `ASYNC_RESET_XZ_VALUE`; deliberately does not distinguish the
    reset-asserted branch from the other one (avoids guessing at polarity
    conventions like `if(rst)` vs `if(!rst_n)` vs `if(rst_n==0)`), and
    deliberately does not attempt a sync-reset block at all, since a
    sync-reset signal has no structural marker to find it by.
    """
    from ..syntax_queries import async_reset_signal_names, is_conditional_statement

    block = enclosing_procedural_block(ctx)
    if block is None:
        return False
    reset_names = async_reset_signal_names(block.raw)
    if not reset_names:
        return False

    for ancestor in reversed(ctx.stack):
        if ancestor is block:
            break
        if is_conditional_statement(ancestor.raw) and _conditional_references_any_name(ancestor.raw, reset_names):
            return True
    return False


def identifier_is_assignment_lhs(ctx: "Context", raw_identifier: SyntaxNode) -> bool:
    _read, write = identifier_access_modes(ctx, raw_identifier)
    return write


def assignment_target_identifier_name(raw: object) -> str | None:
    from ..syntax_queries import identifier_name

    left = assignment_left(raw)
    if left is None:
        return None
    return identifier_name(left)


def assignment_right(raw: object) -> SyntaxNode | None:
    from ..syntax_queries import is_assignment_expression

    if not is_assignment_expression(raw):
        return None
    right = getattr(raw, "right", None)
    return right if isinstance(right, SyntaxNode) else None


def _infer_text_width_and_signed_direct(scope: object, expr_text: str) -> tuple[int | None, bool | None]:
    simple_identifier = simple_identifier_text(expr_text)
    if simple_identifier is not None and scope is not None:
        symbol = getattr(scope, "lookup", lambda _name: None)(simple_identifier)
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
            inner_width, _inner_signed = _infer_text_width_and_signed_direct(scope, replication.group("body"))
            if inner_width is None:
                return None, None
            return int(replication.group("count")) * inner_width, None

        parts = _split_top_level(inner, ",")
        if not parts:
            return None, None
        total = 0
        for part in parts:
            width, _signed = _infer_text_width_and_signed_direct(scope, part)
            if width is None:
                return None, None
            total += width
        return total, None

    return None, None


def simple_expression_width_and_signed(scope: object, expr: SyntaxNode, tree: "SyntaxTree") -> tuple[int | None, bool | None]:
    expr_text = source_text_for_node(expr, tree)
    if expr_text is None:
        return None, None
    return _infer_text_width_and_signed_direct(scope, expr_text)
