from collections.abc import Iterator
import re
from typing import TYPE_CHECKING, cast

import pyslang as sl

from .syntax_kinds import (
    ALWAYS_BLOCK_KIND,
    ALWAYS_COMB_BLOCK_KIND,
    ALWAYS_FF_BLOCK_KIND,
    ALWAYS_LATCH_BLOCK_KIND,
    ASSIGNMENT_KINDS,
    ASSIGN_DEASSIGN_TOKEN_KINDS,
    BLOCK_STATEMENT_KINDS,
    CASE_STATEMENT_KIND,
    CASE_STYLE_TOKEN_KINDS,
    CASE_TOKEN_KINDS,
    CHECKER_DECLARATION_KIND,
    CLOCKING_DECLARATION_KIND,
    CONDITIONAL_STATEMENT_KIND,
    CONTINUOUS_ASSIGN_KIND,
    DISABLE_TOKEN_KIND,
    DO_TOKEN_KIND,
    DO_WHILE_STATEMENT_KIND,
    DEFPARAM_TOKEN_KIND,
    ENDCASE_TOKEN_KIND,
    EVENT_TRIGGER_TOKEN_KINDS,
    FOR_TOKEN_KIND,
    FOREACH_TOKEN_KIND,
    FINAL_BLOCK_KIND,
    FOREVER_TOKEN_KIND,
    FORCE_RELEASE_TOKEN_KINDS,
    INITIAL_BLOCK_KIND,
    INTERFACE_DECLARATION_KIND,
    INSIDE_TOKEN_KIND,
    LOOP_GENERATE_KIND,
    MODPORT_DECLARATION_KIND,
    PARALLEL_BLOCK_STATEMENT_KIND,
    PACKAGE_DECLARATION_KIND,
    PORT_DIRECTION_TOKEN_KINDS,
    PROGRAM_DECLARATION_KIND,
    PROCEDURAL_BLOCK_KINDS,
    READ_WRITE_ASSIGNMENT_KINDS,
    READ_WRITE_UNARY_KINDS,
    REPEAT_TOKEN_KIND,
    SUPPLY0_SUPPLY1_TOKEN_KINDS,
    TASK_DECLARATION_KIND,
    TIMING_CONTROL_STATEMENT_KIND,
    TRANIF_RTRANIF_TOKEN_KINDS,
    TRAN_RTRAN_TOKEN_KINDS,
    TRIREG_TOKEN_KIND,
    UNIQUE0_TOKEN_KIND,
    WAIT_TOKEN_KIND,
    WHILE_TOKEN_KIND,
    WAND_WOR_TOKEN_KINDS,
    UNIQUE_PRIORITY_TOKEN_KINDS,
)
from .types import (
    BinaryEventExpressionNode,
    CaseGenerateNode,
    CaseStatementNode,
    DefaultCaseItemNode,
    IdentifierNameNode,
    IdentifierSelectNameNode,
    IfGenerateNode,
    ImplicitEventControlNode,
    LoopGenerateNode,
    ParenthesizedEventExpressionNode,
    PortDeclarationNode,
    ProceduralBlockNode,
    SignalEventExpressionNode,
    SyntaxNode,
    SyntaxTree,
)

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


def is_continuous_assign(raw: object) -> bool:
    return getattr(raw, "kind", None) == CONTINUOUS_ASSIGN_KIND


def is_initial_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == INITIAL_BLOCK_KIND


def is_final_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == FINAL_BLOCK_KIND


def is_always_latch_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == ALWAYS_LATCH_BLOCK_KIND


def is_always_ff_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == ALWAYS_FF_BLOCK_KIND


def is_always_comb_block(raw: object) -> bool:
    return getattr(raw, "kind", None) == ALWAYS_COMB_BLOCK_KIND


def is_case_generate_node(raw: object) -> bool:
    return isinstance(raw, CaseGenerateNode)


def is_checker_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == CHECKER_DECLARATION_KIND


def is_clocking_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == CLOCKING_DECLARATION_KIND


def is_interface_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == INTERFACE_DECLARATION_KIND


def is_modport_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == MODPORT_DECLARATION_KIND


def is_loop_generate_node(raw: object) -> bool:
    return isinstance(raw, LoopGenerateNode) or getattr(raw, "kind", None) == LOOP_GENERATE_KIND


def is_if_generate_node(raw: object) -> bool:
    return isinstance(raw, IfGenerateNode) or getattr(raw, "kind", None) == getattr(sl.SyntaxKind, "IfGenerate", None)


def is_task_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == TASK_DECLARATION_KIND


def is_program_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == PROGRAM_DECLARATION_KIND


def is_package_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == PACKAGE_DECLARATION_KIND


def is_case_statement(raw: object) -> bool:
    return isinstance(raw, CaseStatementNode) or getattr(raw, "kind", None) == CASE_STATEMENT_KIND


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


def is_disable_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == DISABLE_TOKEN_KIND


def is_do_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == DO_TOKEN_KIND


def is_event_trigger_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in EVENT_TRIGGER_TOKEN_KINDS


def is_for_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == FOR_TOKEN_KIND


def is_foreach_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == FOREACH_TOKEN_KIND


def is_forever_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == FOREVER_TOKEN_KIND


def is_repeat_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == REPEAT_TOKEN_KIND


def is_wait_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == WAIT_TOKEN_KIND


def is_while_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == WHILE_TOKEN_KIND


def is_do_while_statement(raw: object) -> bool:
    return getattr(raw, "kind", None) == DO_WHILE_STATEMENT_KIND


def is_plain_for_token(raw: object, ctx: "Context") -> bool:
    if not is_for_token(raw):
        return False

    return not any(is_loop_generate_node(ancestor.raw) for ancestor in reversed(ctx.stack))


def is_plain_while_token(raw: object, ctx: "Context") -> bool:
    if not is_while_token(raw):
        return False

    return not any(is_do_while_statement(ancestor.raw) for ancestor in reversed(ctx.stack))


def is_case_inside_token(raw: object, tree: SyntaxTree) -> bool:
    if getattr(raw, "kind", None) != INSIDE_TOKEN_KIND:
        return False

    location = getattr(raw, "location", None)
    if location is None:
        return False

    source = tree.sourceManager.getSourceText(location.buffer)
    prefix = source[max(0, location.offset - 32) : location.offset]

    # `case inside (...)` is the only form where the `inside` token is preceded
    # immediately by the `case` keyword in source text. Ordinary `inside`
    # operators have an expression or identifier immediately before them.
    return re.search(r"\bcase\s*$", prefix) is not None


def is_inside_operator_token(raw: object, tree: SyntaxTree) -> bool:
    return getattr(raw, "kind", None) == INSIDE_TOKEN_KIND and not is_case_inside_token(raw, tree)


def _normalized_unique_or_priority(raw: object) -> str | None:
    value = getattr(raw, "uniqueOrPriority", None)
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def case_statement_unique_or_priority(raw: object) -> str | None:
    if not is_case_statement(raw):
        return None
    return _normalized_unique_or_priority(raw)


def conditional_statement_unique_or_priority(raw: object) -> str | None:
    if not is_conditional_statement(raw):
        return None
    return _normalized_unique_or_priority(raw)


def is_unique_priority_case_token(raw: object, ctx: "Context") -> bool:
    if getattr(raw, "kind", None) not in UNIQUE_PRIORITY_TOKEN_KINDS:
        return False

    case_statement = enclosing_case_statement(ctx)
    if case_statement is None:
        return False

    return case_statement_unique_or_priority(case_statement.raw) in {"unique", "priority"}


def is_unique0_case_token(raw: object, ctx: "Context") -> bool:
    if UNIQUE0_TOKEN_KIND is None or getattr(raw, "kind", None) != UNIQUE0_TOKEN_KIND:
        return False

    case_statement = enclosing_case_statement(ctx)
    if case_statement is None:
        return False

    return case_statement_unique_or_priority(case_statement.raw) == "unique0"


def enclosing_conditional_statement(ctx: "Context") -> "BaseVNode | None":
    for ancestor in reversed(ctx.stack):
        if is_conditional_statement(ancestor.raw):
            return ancestor
    return None


def is_unique_if_token(raw: object, ctx: "Context") -> bool:
    if getattr(raw, "kind", None) != sl.TokenKind.UniqueKeyword:
        return False

    conditional_statement = enclosing_conditional_statement(ctx)
    if conditional_statement is None:
        return False

    return conditional_statement_unique_or_priority(conditional_statement.raw) == "unique"


def is_priority_if_token(raw: object, ctx: "Context") -> bool:
    if getattr(raw, "kind", None) != sl.TokenKind.PriorityKeyword:
        return False

    conditional_statement = enclosing_conditional_statement(ctx)
    if conditional_statement is None:
        return False

    return conditional_statement_unique_or_priority(conditional_statement.raw) == "priority"


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


def is_tranif_rtranif_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in TRANIF_RTRANIF_TOKEN_KINDS


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


def declarator_port_direction(ctx: "Context") -> str | None:
    """Return "input" / "output" / "inout" / "ref" for a port declarator, else None."""
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        type_name = type(raw).__name__
        if type_name.endswith("AnsiPortSyntax") or type_name == "PortDeclarationSyntax":
            header = getattr(raw, "header", None)
            direction = getattr(header, "direction", None)
            return PORT_DIRECTION_TOKEN_KINDS.get(getattr(direction, "kind", None))
        if type_name.endswith("DataDeclarationSyntax"):
            return None
    return None


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


def is_parallel_block_statement(raw: object) -> bool:
    return getattr(raw, "kind", None) == PARALLEL_BLOCK_STATEMENT_KIND


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
    for ancestor in reversed(ctx.stack):
        if is_procedural_block(ancestor.raw):
            return ancestor
    return None


def enclosing_continuous_assign(ctx: "Context") -> "BaseVNode | None":
    for ancestor in reversed(ctx.stack):
        if is_continuous_assign(ancestor.raw):
            return ancestor
    return None


def enclosing_case_statement(ctx: "Context") -> "BaseVNode | None":
    for ancestor in reversed(ctx.stack):
        if is_case_statement(ancestor.raw):
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


def iter_identifier_reads(root: SyntaxNode) -> Iterator[tuple[str, SyntaxNode]]:
    """Yield (name, raw_node) for every read-access identifier under `root`, in document
    order. Does not descend into a nested procedural block (there isn't one to reach in
    practice today, but this keeps the walk scoped to the block it started in)."""

    def _walk(node: SyntaxNode, ancestors: list[object]) -> Iterator[tuple[str, SyntaxNode]]:
        if isinstance(node, (IdentifierNameNode, IdentifierSelectNameNode)):
            name = identifier_name(node)
            if name:
                is_read, _is_write = _identifier_access_modes_over_ancestors(ancestors, node)
                if is_read:
                    yield name, node

        ancestors.append(node)
        for child in node:
            if isinstance(child, SyntaxNode) and not isinstance(child, ProceduralBlockNode):
                yield from _walk(child, ancestors)
        ancestors.pop()

    yield from _walk(root, [])


def _iter_identifier_nodes(root: SyntaxNode) -> Iterator[tuple[str, SyntaxNode]]:
    if isinstance(root, (IdentifierNameNode, IdentifierSelectNameNode)):
        name = identifier_name(root)
        if name:
            yield name, root

    for child in root:
        if isinstance(child, SyntaxNode):
            yield from _iter_identifier_nodes(child)


def procedural_block_sensitivity_names(raw: object) -> set[str] | None:
    """For a plain `always @(...)` block, return the set of identifier names in its
    explicit sensitivity list (e.g. `always @(a or b)` -> {"a", "b"}).

    Returns None when there is no explicit list to check against: `always_comb` /
    `always_latch` / `always_ff` blocks (different SyntaxKind entirely), a wildcard
    `always @*` / `always @(*)`, or a list containing any `posedge`/`negedge` qualifier
    (an edge-sensitive block is not subject to the combinational-completeness check --
    a partial list there is the normal, intended pattern).
    """
    if getattr(raw, "kind", None) != ALWAYS_BLOCK_KIND:
        return None

    timing_statement = getattr(raw, "statement", None)
    if getattr(timing_statement, "kind", None) != TIMING_CONTROL_STATEMENT_KIND:
        return None

    event_control = getattr(timing_statement, "timingControl", None)
    if isinstance(event_control, ImplicitEventControlNode):
        return None

    names: set[str] = set()
    has_edge = False

    def _collect(node: object) -> None:
        nonlocal has_edge
        if node is None:
            return
        if isinstance(node, ParenthesizedEventExpressionNode):
            _collect(getattr(node, "expr", None))
        elif isinstance(node, BinaryEventExpressionNode):
            _collect(getattr(node, "left", None))
            _collect(getattr(node, "right", None))
        elif isinstance(node, SignalEventExpressionNode):
            if is_posedge_event(node) or is_negedge_event(node):
                has_edge = True
            expr = getattr(node, "expr", None)
            if isinstance(expr, SyntaxNode):
                for name, _identifier in _iter_identifier_nodes(expr):
                    names.add(name)

    _collect(getattr(event_control, "expr", None))
    if has_edge:
        return None
    return names


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
    "case_statement_unique_or_priority",
    "conditional_statement_unique_or_priority",
    "conditional_statement_body",
    "conditional_statement_has_else",
    "contains_descendant",
    "declarator_has_initializer",
    "declarator_is_port",
    "declarator_name",
    "declarator_port_direction",
    "enclosing_case_statement",
    "enclosing_conditional_statement",
    "enclosing_continuous_assign",
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
    "is_always_ff_block",
    "is_always_latch_block",
    "is_assign_deassign_token",
    "is_assignment_expression",
    "is_block_statement",
    "is_blocking_assignment_token",
    "is_case_generate_keyword_pair",
    "is_case_inside_token",
    "is_case_generate_node",
    "is_case_keyword_token",
    "is_case_statement",
    "is_casex_casez_token",
    "is_checker_declaration_node",
    "is_clocking_declaration_node",
    "is_conditional_statement",
    "is_continuous_assign",
    "is_disable_token",
    "is_do_token",
    "is_do_while_statement",
    "is_defparam_token",
    "is_endcase_token",
    "is_event_trigger_token",
    "is_for_token",
    "is_foreach_token",
    "is_final_block",
    "is_forever_token",
    "is_force_release_token",
    "is_if_generate_node",
    "is_initial_block",
    "is_interface_declaration_node",
    "is_inside_operator_token",
    "is_internal_inout_port_declaration",
    "is_loop_generate_node",
    "is_modport_declaration_node",
    "is_negedge_event",
    "is_nonblocking_assignment_token",
    "is_parallel_block_statement",
    "is_plain_for_token",
    "is_posedge_event",
    "is_priority_if_token",
    "is_package_declaration_node",
    "is_program_declaration_node",
    "is_plain_while_token",
    "is_procedural_block",
    "is_read_write_assignment_expression",
    "is_read_write_unary_expression",
    "is_repeat_token",
    "is_supply0_supply1_token",
    "is_task_declaration_node",
    "is_tranif_rtranif_token",
    "is_tran_rtran_token",
    "is_trireg_token",
    "is_unique0_case_token",
    "is_unique_if_token",
    "is_unique_priority_case_token",
    "is_wait_token",
    "is_while_token",
    "is_wand_wor_token",
    "iter_assignment_nodes",
    "iter_identifier_reads",
    "iter_statement_nodes",
    "module_declaration_name",
    "procedural_block_sensitivity_names",
    "procedural_block_statement",
    "unary_write_operand",
]
