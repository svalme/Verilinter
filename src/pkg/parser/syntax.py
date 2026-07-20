from collections.abc import Iterator
from typing import TYPE_CHECKING

import pyslang as sl

from .types import CaseGenerateNode, DefaultCaseItemNode, PortDeclarationNode, ProceduralBlockNode, SyntaxNode, SyntaxTree

if TYPE_CHECKING:
    from ..vnodes.base_vnode import BaseVNode
    from ..walk.context import Context


def _syntax_kind(name: str) -> object | None:
    return getattr(sl.SyntaxKind, name, None)


ALWAYS_BLOCK_KIND = sl.SyntaxKind.AlwaysBlock
ALWAYS_COMB_BLOCK_KIND = sl.SyntaxKind.AlwaysCombBlock
ALWAYS_LATCH_BLOCK_KIND = sl.SyntaxKind.AlwaysLatchBlock
INITIAL_BLOCK_KIND = sl.SyntaxKind.InitialBlock
FINAL_BLOCK_KIND = sl.SyntaxKind.FinalBlock
ENDCASE_TOKEN_KIND = sl.TokenKind.EndCaseKeyword
CASE_TOKEN_KINDS = {
    sl.TokenKind.CaseKeyword,
    sl.TokenKind.CaseXKeyword,
    sl.TokenKind.CaseZKeyword,
}

SIMPLE_ASSIGNMENT_KINDS = {
    sl.SyntaxKind.AssignmentExpression,
    sl.SyntaxKind.NonblockingAssignmentExpression,
}

READ_WRITE_ASSIGNMENT_KINDS = {
    kind
    for kind in (
        _syntax_kind("AddAssignmentExpression"),
        _syntax_kind("SubAssignmentExpression"),
        _syntax_kind("MulAssignmentExpression"),
        _syntax_kind("DivAssignmentExpression"),
        _syntax_kind("ModAssignmentExpression"),
        _syntax_kind("AndAssignmentExpression"),
        _syntax_kind("OrAssignmentExpression"),
        _syntax_kind("XorAssignmentExpression"),
        _syntax_kind("LogicalShiftLeftAssignmentExpression"),
        _syntax_kind("LogicalShiftRightAssignmentExpression"),
        _syntax_kind("ArithmeticShiftLeftAssignmentExpression"),
        _syntax_kind("ArithmeticShiftRightAssignmentExpression"),
    )
    if kind is not None
}

READ_WRITE_UNARY_KINDS = {
    kind
    for kind in (
        _syntax_kind("UnaryPreincrementExpression"),
        _syntax_kind("UnaryPredecrementExpression"),
        _syntax_kind("PostincrementExpression"),
        _syntax_kind("PostdecrementExpression"),
    )
    if kind is not None
}

ASSIGNMENT_KINDS = SIMPLE_ASSIGNMENT_KINDS | READ_WRITE_ASSIGNMENT_KINDS

PROCEDURAL_BLOCK_KINDS = {
    ALWAYS_BLOCK_KIND,
    ALWAYS_COMB_BLOCK_KIND,
    ALWAYS_LATCH_BLOCK_KIND,
    INITIAL_BLOCK_KIND,
    FINAL_BLOCK_KIND,
}

CASE_STYLE_TOKEN_KINDS = {
    sl.TokenKind.CaseXKeyword,
    sl.TokenKind.CaseZKeyword,
}

UNIQUE_PRIORITY_TOKEN_KINDS = {
    sl.TokenKind.UniqueKeyword,
    sl.TokenKind.PriorityKeyword,
}


def is_assignment_expression(raw: object) -> bool:
    return getattr(raw, "kind", None) in ASSIGNMENT_KINDS


def is_read_write_assignment_expression(raw: object) -> bool:
    return getattr(raw, "kind", None) in READ_WRITE_ASSIGNMENT_KINDS


def is_read_write_unary_expression(raw: object) -> bool:
    return getattr(raw, "kind", None) in READ_WRITE_UNARY_KINDS


def is_procedural_block(raw: object) -> bool:
    return isinstance(raw, ProceduralBlockNode) or getattr(raw, "kind", None) in PROCEDURAL_BLOCK_KINDS


def is_initial_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == INITIAL_BLOCK_KIND


def is_final_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == FINAL_BLOCK_KIND


def is_always_latch_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == ALWAYS_LATCH_BLOCK_KIND


def is_case_generate_node(raw: object) -> bool:
    return isinstance(raw, CaseGenerateNode)


def is_internal_inout_port_declaration(raw: object) -> bool:
    if not isinstance(raw, PortDeclarationNode):
        return False
    header = getattr(raw, "header", None)
    direction = getattr(header, "direction", None)
    return getattr(direction, "kind", None) == sl.TokenKind.InOutKeyword


def is_blocking_assignment_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == sl.TokenKind.Equals


def is_nonblocking_assignment_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == sl.TokenKind.LessThanEquals


def is_casex_casez_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in CASE_STYLE_TOKEN_KINDS


def is_case_keyword_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in CASE_TOKEN_KINDS


def is_unique_priority_case_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in UNIQUE_PRIORITY_TOKEN_KINDS


def is_endcase_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == ENDCASE_TOKEN_KIND


def is_case_generate_keyword_pair(raw: object) -> bool:
    return str(getattr(raw, "keyword", "")).strip() == "case" and str(getattr(raw, "endCase", "")).strip() == "endcase"


def has_default_case_item(raw: object) -> bool:
    items = getattr(raw, "items", [])
    return any(isinstance(item, DefaultCaseItemNode) for item in items)


def is_posedge_event(raw: object) -> bool:
    return str(getattr(raw, "edge", "")) == "posedge"


def is_negedge_event(raw: object) -> bool:
    return str(getattr(raw, "edge", "")) == "negedge"


def module_declaration_name(raw: object) -> str | None:
    header = getattr(raw, "header", None)
    name = getattr(header, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def declarator_name(raw: object) -> str | None:
    name = getattr(raw, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def declarator_has_initializer(raw: object) -> bool:
    return getattr(raw, "initializer", None) is not None


def instantiation_type_name(raw: object) -> str | None:
    type_node = getattr(raw, "type", None)
    value = getattr(type_node, "value", None)
    return value if isinstance(value, str) and value else None


def hierarchical_instance_name(raw: object) -> str | None:
    decl = getattr(raw, "decl", None)
    name = getattr(decl, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def identifier_name(raw: object) -> str | None:
    identifier = getattr(raw, "identifier", None)
    value = getattr(identifier, "value", None)
    return value if isinstance(value, str) and value else None


def has_full_parallel_case_pragma(raw: object, tree: SyntaxTree) -> bool:
    if not is_case_keyword_token(raw):
        return False

    location = getattr(raw, "location", None)
    if location is None:
        return False

    source_manager = tree.sourceManager
    source = source_manager.getSourceText(location.buffer)
    line_number = source_manager.getLineNumber(location)
    lines = source.splitlines()
    if line_number <= 1 or line_number - 2 >= len(lines):
        return False

    preceding_line = lines[line_number - 2].lower()
    return "full_case" in preceding_line or "parallel_case" in preceding_line


def contains_descendant(root: SyntaxNode, target: SyntaxNode) -> bool:
    if root is target:
        return True
    for child in root:
        if isinstance(child, SyntaxNode) and contains_descendant(child, target):
            return True
    return False


def assignment_left(raw: object) -> SyntaxNode | None:
    if not is_assignment_expression(raw):
        return None
    left = getattr(raw, "left", None)
    return left if isinstance(left, SyntaxNode) else None


def unary_write_operand(raw: object) -> SyntaxNode | None:
    if not is_read_write_unary_expression(raw):
        return None
    operand = getattr(raw, "operand", None)
    return operand if isinstance(operand, SyntaxNode) else None


def identifier_access_modes(ctx: "Context", raw_identifier: SyntaxNode) -> tuple[bool, bool]:
    for ancestor in reversed(ctx.stack):
        left = assignment_left(ancestor.raw)
        if left is not None and contains_descendant(left, raw_identifier):
            if is_read_write_assignment_expression(ancestor.raw):
                return True, True
            return False, True

        operand = unary_write_operand(ancestor.raw)
        if operand is not None and contains_descendant(operand, raw_identifier):
            return True, True

    return True, False


def enclosing_procedural_block(ctx: "Context") -> "BaseVNode | None":
    for ancestor in reversed(ctx.stack):
        if is_procedural_block(ancestor.raw):
            return ancestor
    return None


def identifier_is_assignment_lhs(ctx: "Context", raw_identifier: SyntaxNode) -> bool:
    _read, write = identifier_access_modes(ctx, raw_identifier)
    return write


def iter_assignment_nodes(node: SyntaxNode) -> Iterator[SyntaxNode]:
    if is_assignment_expression(node):
        yield node

    for child in node:
        if not isinstance(child, SyntaxNode):
            continue
        if isinstance(child, ProceduralBlockNode):
            continue
        yield from iter_assignment_nodes(child)
