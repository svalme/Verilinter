from collections.abc import Iterator
import re

from ..syntax_kinds import (
    BLOCK_STATEMENT_KINDS,
    CASE_TOKEN_KINDS,
    COMPILATION_UNIT_KIND,
    CONDITIONAL_STATEMENT_KIND,
    ELSE_CLAUSE_KIND,
    GENERATE_BLOCK_KIND,
    MODULE_DECLARATION_KIND,
    PARALLEL_BLOCK_STATEMENT_KIND,
    PORT_DIRECTION_TOKEN_KINDS,
)
from ..types import SyntaxNode, SyntaxTree
from .shared import type_text_width_and_signed


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


def declarator_is_parameter(ctx: "Context") -> bool:
    """True if the declarator being processed belongs to a `parameter`/`localparam`
    declaration (`ParameterDeclarationSyntax`) rather than an ordinary net/variable
    declaration or a port. Both `parameter` and `localparam` share this same node
    kind -- pyslang distinguishes them only via the declaration's own `keyword`
    field, which this project's rules have no current need to tell apart."""
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        type_name = type(raw).__name__
        if type_name == "ParameterDeclarationSyntax":
            return True
        if type_name.endswith("DataDeclarationSyntax") or type_name.endswith("AnsiPortSyntax") or type_name == "PortDeclarationSyntax":
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


def hierarchical_instance_list(raw: object) -> list[SyntaxNode]:
    """Return the instance nodes under a `HierarchyInstantiationSyntax`, or `[]`
    if the node has no recognizable instance list."""
    items = getattr(raw, "instances", None)
    if items is None:
        return []
    return [item for item in items if isinstance(item, SyntaxNode)]


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


def is_else_clause_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == ELSE_CLAUSE_KIND


def else_clause_body(raw: object) -> SyntaxNode | None:
    clause = getattr(raw, "clause", None)
    return clause if isinstance(clause, SyntaxNode) else None


def is_unwrapped_if_body(raw: object) -> bool:
    """True if a ConditionalStatementSyntax's `if` branch is a single statement
    not wrapped in begin/end."""
    if not is_conditional_statement(raw):
        return False
    body = conditional_statement_body(raw)
    return isinstance(body, SyntaxNode) and not is_block_statement(body)


def is_unwrapped_else_body(raw: object) -> bool:
    """True if an ElseClauseSyntax's body is a single statement not wrapped in
    begin/end and not itself an `else if` chain."""
    if not is_else_clause_node(raw):
        return False
    body = else_clause_body(raw)
    return (
        isinstance(body, SyntaxNode)
        and not is_block_statement(body)
        and not is_conditional_statement(body)
    )


def is_parallel_block_statement(raw: object) -> bool:
    return getattr(raw, "kind", None) == PARALLEL_BLOCK_STATEMENT_KIND


def iter_statement_nodes(raw: SyntaxNode) -> Iterator[SyntaxNode]:
    if not is_block_statement(raw):
        yield raw
        return

    items = getattr(raw, "items", None)
    if items is None:
        return

    for child in items:
        if isinstance(child, SyntaxNode):
            yield child


def expression_statement_expression(raw: object) -> SyntaxNode | None:
    expr = getattr(raw, "expr", None)
    return expr if isinstance(expr, SyntaxNode) else None


def has_full_parallel_case_pragma(raw: object, tree: SyntaxTree) -> bool:
    if getattr(raw, "kind", None) not in CASE_TOKEN_KINDS:
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


def is_module_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == MODULE_DECLARATION_KIND


def is_first_module_declaration_in_file(raw: object, tree: SyntaxTree) -> bool:
    if not is_module_declaration_node(raw):
        return False
    root = tree.root
    if getattr(root, "kind", None) == COMPILATION_UNIT_KIND:
        members = getattr(root, "members", None)
        if members is None:
            return False
        for member in members:
            if getattr(member, "kind", None) == MODULE_DECLARATION_KIND:
                return member is raw
        return False
    return root is raw


TIMESCALE_DIRECTIVE_RE = re.compile(r"`timescale\b")


def has_timescale_directive_before(raw: object, tree: SyntaxTree) -> bool:
    source_range = getattr(raw, "sourceRange", None)
    start = getattr(source_range, "start", None)
    if start is None:
        return False
    source = tree.sourceManager.getSourceText(start.buffer)
    return TIMESCALE_DIRECTIVE_RE.search(source[: start.offset]) is not None


def is_missing_timescale_directive(raw: object, tree: SyntaxTree) -> bool:
    return is_first_module_declaration_in_file(raw, tree) and not has_timescale_directive_before(raw, tree)


def _declarator_owner_type_text(ctx: "Context") -> str | None:
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        type_name = type(raw).__name__
        if type_name.endswith("AnsiPortSyntax") or type_name == "PortDeclarationSyntax":
            header = getattr(raw, "header", None)
            return str(header).strip() if header is not None else None
        if type_name.endswith("DataDeclarationSyntax"):
            data_type = getattr(raw, "type", None)
            return str(data_type).strip() if data_type is not None else None
    return None


def declarator_bit_width(ctx: "Context") -> int | None:
    type_text = _declarator_owner_type_text(ctx)
    width, _signed = type_text_width_and_signed(type_text)
    return width


def declarator_is_signed(ctx: "Context") -> bool | None:
    type_text = _declarator_owner_type_text(ctx)
    _width, signed = type_text_width_and_signed(type_text)
    return signed


def is_generate_block_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == GENERATE_BLOCK_KIND


def is_unlabeled_generate_block(raw: object) -> bool:
    """True if `raw` is a `GenerateBlockSyntax` (the `begin ... end` body of an
    if/loop/case-generate branch, or a bare nested block directly inside a
    `generate` region) with no `: label` on its `begin`.

    An unlabeled generate block still gets an implicit `genblkN` name during
    elaboration, but that name is index-based and shifts if a sibling branch is
    added or removed -- an explicit label keeps hierarchical paths (and
    waveform/debug views) stable. The unwrapped single-statement generate body
    (`if (cond) wire w;`, no `begin`/`end` at all) is a different, unnamed shape
    entirely -- it never becomes a `GenerateBlockSyntax`, so it is intentionally
    not covered here.
    """
    return is_generate_block_node(raw) and getattr(raw, "beginName", None) is None


def named_port_connection_name(raw: object) -> str | None:
    name = getattr(raw, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def port_connection_expression(raw: object) -> SyntaxNode | None:
    expr = getattr(raw, "expr", None)
    return expr if isinstance(expr, SyntaxNode) else None


def parameter_override_list(raw: object) -> list[SyntaxNode]:
    """Return the individual parameter-override syntax nodes from a
    `HierarchyInstantiationSyntax.parameters` field (`#(...)`), or `[]` if the
    instantiation has no parameter override list at all."""
    param_assignment = getattr(raw, "parameters", None)
    if param_assignment is None:
        return []
    items = getattr(param_assignment, "parameters", None)
    if items is None:
        return []
    return [item for item in items if isinstance(item, SyntaxNode)]


def port_connection_list(raw: object) -> list[SyntaxNode]:
    """Return the per-port connection nodes from a
    `HierarchicalInstanceSyntax.connections` field, or `[]` when absent."""
    items = getattr(raw, "connections", None)
    if items is None:
        return []
    return [item for item in items if isinstance(item, SyntaxNode)]


def is_named_parameter_override(raw: object) -> bool:
    return type(raw).__name__ == "NamedParamAssignmentSyntax"


def is_ordered_parameter_override(raw: object) -> bool:
    return type(raw).__name__ == "OrderedParamAssignmentSyntax"


def named_parameter_override_name(raw: object) -> str | None:
    name = getattr(raw, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None
