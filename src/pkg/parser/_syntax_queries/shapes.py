from collections.abc import Iterator
import re

from ..syntax_kinds import (
    BIT_SELECT_KIND,
    BLOCK_STATEMENT_KINDS,
    CASE_TOKEN_KINDS,
    COMPILATION_UNIT_KIND,
    CONDITIONAL_STATEMENT_KIND,
    ELSE_CLAUSE_KIND,
    EMPTY_STATEMENT_KIND,
    GENERATE_BLOCK_KIND,
    MODULE_DECLARATION_KIND,
    PARALLEL_BLOCK_STATEMENT_KIND,
    PORT_DIRECTION_TOKEN_KINDS,
    RANGE_SELECT_KINDS,
)
from ..types import IdentifierSelectNameNode, SyntaxNode, SyntaxTree
from .shared import simple_packed_range, type_text_width_and_signed


def declarator_name(raw: object) -> str | None:
    name = getattr(raw, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def declarator_has_initializer(raw: object) -> bool:
    return getattr(raw, "initializer", None) is not None


def declarator_initializer_value(raw: object) -> int | None:
    """Return a declarator's initializer expression constant-folded to an
    `int` (via `constant_integer_value`), else `None` -- used to populate
    `Symbol.value` for `parameter`/`localparam` declarators whose RHS is a
    simple resolvable constant."""
    from ..syntax_queries import constant_integer_value

    initializer = getattr(raw, "initializer", None)
    expr = getattr(initializer, "expr", None)
    if expr is None:
        return None
    return constant_integer_value(expr)


def declarator_initializer_expression(raw: object) -> SyntaxNode | None:
    initializer = getattr(raw, "initializer", None)
    expr = getattr(initializer, "expr", None)
    return expr if isinstance(expr, SyntaxNode) else None



def declarator_is_port(ctx: "Context") -> bool:
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        type_name = type(raw).__name__
        if type_name.endswith("AnsiPortSyntax") or type_name in ("PortDeclarationSyntax", "FunctionPortSyntax"):
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


def _explicit_port_direction(raw: object) -> str | None:
    header = getattr(raw, "header", None)
    direction = getattr(header, "direction", None)
    return PORT_DIRECTION_TOKEN_KINDS.get(getattr(direction, "kind", None))


def _ansi_port_list_items(list_node: object) -> list[object]:
    """Flatten an `AnsiPortListSyntax` down to its ordered `ImplicitAnsiPortSyntax`
    items, looking through the intermediate separated-list wrapper pyslang puts
    between the list and its items."""
    items: list[object] = []

    def _walk(node: object) -> None:
        for child in node:
            if not isinstance(child, SyntaxNode):
                continue
            if type(child).__name__.endswith("AnsiPortSyntax"):
                items.append(child)
            else:
                _walk(child)

    _walk(list_node)
    return items


def _inherited_port_direction(raw: object) -> str | None:
    """A port that omits its own direction keyword (`input clk, wen,` -- `wen`
    has no keyword of its own) inherits the *previous* port's direction in the
    same ANSI port list. pyslang models this literally: `wen`'s own
    `ImplicitAnsiPortSyntax.header.direction` is an empty token, not a copy of
    `clk`'s. This scans
    backward through the enclosing port list's ordered items for the nearest
    preceding one that does carry an explicit direction."""
    parent = getattr(raw, "parent", None)
    if parent is None:
        return None
    siblings = _ansi_port_list_items(parent)
    try:
        index = next(i for i, sibling in enumerate(siblings) if sibling is raw)
    except StopIteration:
        return None
    for sibling in reversed(siblings[:index]):
        direction = _explicit_port_direction(sibling)
        if direction is not None:
            return direction
    return None


def declarator_port_direction(ctx: "Context") -> str | None:
    """Return "input" / "output" / "inout" / "ref" for a port declarator, else
    None. Falls back to `_inherited_port_direction` for an ANSI port that
    shares a preceding port's direction keyword instead of repeating it."""
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        type_name = type(raw).__name__
        if type_name == "FunctionPortSyntax":
            # Function/task ANSI arguments default to input and inherit omitted
            # directions from earlier arguments in the same prototype.
            direction = "input"
            for port in raw.parent.ports:
                if type(port).__name__ != "FunctionPortSyntax":
                    continue
                direction = PORT_DIRECTION_TOKEN_KINDS.get(port.direction.kind, direction)
                if port is raw:
                    return direction
            return direction
        if type_name.endswith("AnsiPortSyntax") or type_name == "PortDeclarationSyntax":
            direction = _explicit_port_direction(raw)
            if direction is not None:
                return direction
            return _inherited_port_direction(raw)
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


def conditional_statement_else_body(raw: object) -> SyntaxNode | None:
    else_clause = getattr(raw, "elseClause", None)
    if else_clause is None:
        return None
    return else_clause_body(else_clause)



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


def is_extra_module_declaration_in_file(raw: object, tree: SyntaxTree) -> bool:
    if not is_module_declaration_node(raw):
        return False
    root = tree.root
    if getattr(root, "kind", None) != COMPILATION_UNIT_KIND:
        return False
    members = getattr(root, "members", None)
    if members is None:
        return False
    seen_first = False
    for member in members:
        if getattr(member, "kind", None) != MODULE_DECLARATION_KIND:
            continue
        if not seen_first:
            seen_first = True
            continue
        if member is raw:
            return True
    return False


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
        if type_name.endswith("DataDeclarationSyntax") or type_name.endswith("NetDeclarationSyntax"):
            # Both node kinds expose their packed-dimension text via `.type`
            # (e.g. `reg [7:0]` / ` [7:0]` for a `wire [7:0]` -- the `wire`
            # keyword itself lives in NetDeclarationSyntax's separate
            # `.netType` field, not `.type`, but `type_text_width_and_signed`
            # only needs the bracket range so that's irrelevant here).
            # Both `DataDeclarationSyntax` (`reg`/`logic`/plain variable
            # declarations) and `NetDeclarationSyntax` (`wire [N:0] sig;`) carry
            # the bracket range.
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


def declarator_packed_range(ctx: "Context") -> tuple[int | None, int | None]:
    type_text = _declarator_owner_type_text(ctx)
    return simple_packed_range(type_text)


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


def _generate_block_label(raw: object) -> str | None:
    if not is_generate_block_node(raw):
        return None
    begin_name = getattr(raw, "beginName", None)
    value = getattr(getattr(begin_name, "name", None), "value", None)
    return value if isinstance(value, str) and value else None


def duplicate_generate_branch_label(raw: object) -> bool:
    """True if `raw` (an `IfGenerateSyntax` or `CaseGenerateSyntax`) has two or
    more direct generate-block branches sharing the same explicit label --
    the `if`/`else` branches of one if-generate, or the case items of one
    case-generate. An unlabeled branch (`MISSING_GENERATE_BLOCK_LABEL`'s own
    concern) is never compared against anything here, since two unlabeled
    branches are not a genuine name collision.

    Deliberately per-construct, matching `is_unlabeled_generate_block`'s own
    anchoring: two labels colliding across two separate top-level
    `generate...endgenerate` regions in the same module are a real
    elaboration-time hierarchical-path collision too, but that needs
    module-wide generate-label collection this first pass doesn't attempt.
    """
    from .node_kind_checks import is_case_generate_node, is_if_generate_node

    labels: list[str] = []
    if is_if_generate_node(raw):
        block_label = _generate_block_label(getattr(raw, "block", None))
        if block_label is not None:
            labels.append(block_label)
        else_clause = getattr(raw, "elseClause", None)
        else_label = _generate_block_label(getattr(else_clause, "clause", None))
        if else_label is not None:
            labels.append(else_label)
    elif is_case_generate_node(raw):
        for item in getattr(raw, "items", None) or []:
            label = _generate_block_label(getattr(item, "clause", None))
            if label is not None:
                labels.append(label)
    else:
        return False

    return len(labels) != len(set(labels))


def is_empty_conditional_or_case_branch(raw: object) -> bool:
    """True if `raw` is an empty `begin...end` block or a bare `;`
    (`EmptyStatementSyntax`) sitting directly in an if/else/case-item branch
    position -- `ConditionalStatementSyntax.statement`, `ElseClauseSyntax.clause`,
    or a case item's `.clause`. Needs no ancestor walk, same one-level-up
    `.parent` check style as `is_unsized_literal_in_flagged_value_context`.
    """
    kind = getattr(raw, "kind", None)
    if kind == EMPTY_STATEMENT_KIND:
        is_empty = True
    elif is_block_statement(raw):
        items = getattr(raw, "items", None)
        is_empty = next(iter(items), None) is None if items is not None else True
    else:
        return False
    if not is_empty:
        return False

    parent = getattr(raw, "parent", None)
    parent_type = type(parent).__name__
    if parent_type == "ConditionalStatementSyntax":
        return getattr(parent, "statement", None) is raw
    if parent_type == "ElseClauseSyntax":
        return getattr(parent, "clause", None) is raw
    if parent_type in ("StandardCaseItemSyntax", "DefaultCaseItemSyntax"):
        return getattr(parent, "clause", None) is raw
    return False


def identifier_select_base_and_selectors(raw: object) -> tuple[str, list[SyntaxNode]] | None:
    """Return `(base_name, selectors)` for an `IdentifierSelectNameSyntax`
    (`a[2]`, `a[6:3]`, `a[3+:4]`) -- its base identifier name plus the list of
    `ElementSelectSyntax` selector nodes -- else `None`."""
    if not isinstance(raw, IdentifierSelectNameNode):
        return None
    identifier = getattr(raw, "identifier", None)
    name = getattr(identifier, "value", None)
    if not isinstance(name, str) or not name:
        return None
    selectors = getattr(raw, "selectors", None)
    if selectors is None:
        return None
    return name, [selector for selector in selectors if isinstance(selector, SyntaxNode)]


def element_select_index_or_range(
    selector: object,
) -> tuple[str, object] | None:
    """Unwrap one `ElementSelectSyntax` selector into a `(shape, payload)` pair:
    `("bit", expr)` for `a[N]`, or `("simple_range" | "ascending" | "descending",
    (left, right))` for `a[M:L]` / `a[base+:W]` / `a[base-:W]`. Else `None`.
    """
    inner = getattr(selector, "selector", None)
    inner_kind = getattr(inner, "kind", None)
    if inner_kind == BIT_SELECT_KIND:
        expr = getattr(inner, "expr", None)
        return ("bit", expr) if isinstance(expr, SyntaxNode) else None
    if inner_kind in RANGE_SELECT_KINDS:
        left = getattr(inner, "left", None)
        right = getattr(inner, "right", None)
        if not isinstance(left, SyntaxNode) or not isinstance(right, SyntaxNode):
            return None
        shape = {
            "SimpleRangeSelect": "simple_range",
            "AscendingRangeSelect": "ascending",
            "DescendingRangeSelect": "descending",
        }.get(str(inner_kind).rsplit(".", 1)[-1])
        return (shape, (left, right)) if shape is not None else None
    return None


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


def is_port_connection_node(raw: object) -> bool:
    """True for a `NamedPortConnectionSyntax`/`OrderedPortConnectionSyntax`
    node -- one entry of a `HierarchicalInstanceSyntax.connections` list (see
    `port_connection_list`). Used by `enclosing_port_connection` to tell an
    identifier used to wire a net into an instance port apart from an
    ordinary read/write, since the connected port's direction (which side is
    actually driving the net) generally isn't resolvable at the point a
    single file is walked -- the instantiated module may be defined in
    another file, or simply not yet visited."""
    return type(raw).__name__ in ("NamedPortConnectionSyntax", "OrderedPortConnectionSyntax")


def is_named_parameter_override(raw: object) -> bool:
    return type(raw).__name__ == "NamedParamAssignmentSyntax"


def is_ordered_parameter_override(raw: object) -> bool:
    return type(raw).__name__ == "OrderedParamAssignmentSyntax"


def named_parameter_override_name(raw: object) -> str | None:
    name = getattr(raw, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def resolve_assignment_target_and_rhs(vnode: object, ctx: object):
    """Unpack an assignment-like construct -- continuous assignment, procedural
    assignment, or variable declarator initializer -- returning
    `(lhs_symbol, right_expr)` resolved against `ctx.scope()`.
    Returns `(None, None)` when the construct is not an assignment or the
    target cannot be resolved.
    """
    from ..syntax_queries import (
        assignment_left,
        assignment_right,
        is_assignment_expression,
    )

    raw = getattr(vnode, "raw", vnode)
    scope = getattr(ctx, "scope", lambda: None)()

    if is_assignment_expression(raw):
        left = assignment_left(raw)
        right = assignment_right(raw)
        if left is None or right is None:
            return None, None
        name = identifier_name(left)
        if name is None or scope is None:
            return None, None
        lookup_hierarchical = getattr(scope, "lookup_hierarchical", None)
        symbol = lookup_hierarchical(name) if callable(lookup_hierarchical) else getattr(scope, "lookup", lambda _n: None)(name)
        return symbol, right

    if declarator_has_initializer(raw):
        if declarator_is_parameter(ctx):
            return None, None
        name = declarator_name(raw)
        if name is None or scope is None:
            return None, None
        lookup_hierarchical = getattr(scope, "lookup_hierarchical", None)
        symbol = lookup_hierarchical(name) if callable(lookup_hierarchical) else getattr(scope, "lookup", lambda _n: None)(name)
        right = declarator_initializer_expression(raw)
        return symbol, right

    return None, None

