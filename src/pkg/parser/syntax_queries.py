from collections.abc import Iterator
from typing import TYPE_CHECKING, cast

import pyslang as sl

from .syntax_kinds import (
    ALWAYS_COMB_BLOCK_KIND,
    ALWAYS_LATCH_BLOCK_KIND,
    ASSIGNMENT_KINDS,
    ASSIGN_DEASSIGN_TOKEN_KINDS,
    BLOCK_STATEMENT_KINDS,
    CASE_STYLE_TOKEN_KINDS,
    CASE_TOKEN_KINDS,
    CONDITIONAL_STATEMENT_KIND,
    DEFPARAM_TOKEN_KIND,
    ENDCASE_TOKEN_KIND,
    FINAL_BLOCK_KIND,
    FORCE_RELEASE_TOKEN_KINDS,
    INITIAL_BLOCK_KIND,
    PROCEDURAL_BLOCK_KINDS,
    READ_WRITE_ASSIGNMENT_KINDS,
    READ_WRITE_UNARY_KINDS,
    SUPPLY0_SUPPLY1_TOKEN_KINDS,
    TRAN_RTRAN_TOKEN_KINDS,
    TRIREG_TOKEN_KIND,
    WAND_WOR_TOKEN_KINDS,
    UNIQUE_PRIORITY_TOKEN_KINDS,
)
from .types import CaseGenerateNode, DefaultCaseItemNode, PortDeclarationNode, ProceduralBlockNode, SyntaxNode, SyntaxTree

if TYPE_CHECKING:
    from ..vnodes.base_vnode import BaseVNode
    from ..walk.context import Context


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


def is_always_comb_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == ALWAYS_COMB_BLOCK_KIND


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


def is_defparam_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == DEFPARAM_TOKEN_KIND


def is_force_release_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in FORCE_RELEASE_TOKEN_KINDS


def is_assign_deassign_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in ASSIGN_DEASSIGN_TOKEN_KINDS


def is_wand_wor_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in WAND_WOR_TOKEN_KINDS


def is_trireg_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == TRIREG_TOKEN_KIND


def is_supply0_supply1_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in SUPPLY0_SUPPLY1_TOKEN_KINDS


def is_tran_rtran_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in TRAN_RTRAN_TOKEN_KINDS


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


def declarator_is_port(ctx: "Context") -> bool:
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        type_name = type(raw).__name__
        if type_name.endswith("AnsiPortSyntax") or type_name == "PortDeclarationSyntax":
            return True
        if type_name.endswith("DataDeclarationSyntax"):
            return False
    return False


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


def procedural_block_statement(raw: object) -> SyntaxNode | None:
    statement = getattr(raw, "statement", None)
    return statement if isinstance(statement, SyntaxNode) else None


def is_conditional_statement(raw: object) -> bool:
    return getattr(raw, "kind", None) == CONDITIONAL_STATEMENT_KIND


def conditional_statement_has_else(raw: object) -> bool:
    return getattr(raw, "elseClause", None) is not None


def conditional_statement_body(raw: object) -> SyntaxNode | None:
    statement = getattr(raw, "statement", None)
    return statement if isinstance(statement, SyntaxNode) else None


def is_block_statement(raw: object) -> bool:
    return getattr(raw, "kind", None) in BLOCK_STATEMENT_KINDS


def iter_statement_nodes(raw: SyntaxNode) -> Iterator[SyntaxNode]:
    if not is_block_statement(raw):
        yield raw
        return

    items = getattr(raw, "items", None)
    if items is None:
        return

    for child in cast(SyntaxNode, items):
        if isinstance(child, SyntaxNode):
            yield child


def expression_statement_expression(raw: object) -> SyntaxNode | None:
    expr = getattr(raw, "expr", None)
    return expr if isinstance(expr, SyntaxNode) else None


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


def assignment_target_identifier_name(raw: object) -> str | None:
    left = assignment_left(raw)
    if left is None:
        return None
    return identifier_name(left)


def iter_assignment_nodes(node: SyntaxNode) -> Iterator[SyntaxNode]:
    if is_assignment_expression(node):
        yield node

    for child in node:
        if not isinstance(child, SyntaxNode):
            continue
        if isinstance(child, ProceduralBlockNode):
            continue
        yield from iter_assignment_nodes(child)


__all__ = [
    "assignment_left",
    "assignment_target_identifier_name",
    "conditional_statement_body",
    "conditional_statement_has_else",
    "contains_descendant",
    "declarator_has_initializer",
    "declarator_is_port",
    "declarator_name",
    "enclosing_procedural_block",
    "expression_statement_expression",
    "has_default_case_item",
    "has_full_parallel_case_pragma",
    "hierarchical_instance_name",
    "identifier_access_modes",
    "identifier_is_assignment_lhs",
    "identifier_name",
    "instantiation_type_name",
    "is_always_comb_block",
    "is_always_latch_block",
    "is_assign_deassign_token",
    "is_assignment_expression",
    "is_block_statement",
    "is_blocking_assignment_token",
    "is_case_generate_keyword_pair",
    "is_case_generate_node",
    "is_case_keyword_token",
    "is_casex_casez_token",
    "is_conditional_statement",
    "is_defparam_token",
    "is_endcase_token",
    "is_final_block",
    "is_force_release_token",
    "is_initial_block",
    "is_internal_inout_port_declaration",
    "is_negedge_event",
    "is_nonblocking_assignment_token",
    "is_posedge_event",
    "is_procedural_block",
    "is_read_write_assignment_expression",
    "is_read_write_unary_expression",
    "is_supply0_supply1_token",
    "is_tran_rtran_token",
    "is_trireg_token",
    "is_unique_priority_case_token",
    "is_wand_wor_token",
    "iter_assignment_nodes",
    "iter_statement_nodes",
    "module_declaration_name",
    "procedural_block_statement",
    "unary_write_operand",
]
