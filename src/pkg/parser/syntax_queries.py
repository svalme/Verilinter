import re
from pathlib import PurePath
from typing import TYPE_CHECKING

import pyslang as sl

from ._syntax_queries.shared import (
    node_location,
    raw_node_children,
    simple_identifier_text,
    simple_packed_width,
    source_text_for_node,
    syntax_node_snippet,
    token_location,
    token_raw_text,
    type_text_width_and_signed,
)
from ._syntax_queries.access import (
    assignment_left,
    assignment_right,
    assignment_target_identifier_name,
    contains_descendant,
    enclosing_case_statement,
    enclosing_continuous_assign,
    enclosing_primitive_instantiation,
    enclosing_procedural_block,
    identifier_access_modes,
    identifier_is_assignment_lhs,
    is_combinational_driver_block,
    simple_expression_width_and_signed,
    unary_write_operand,
)
from ._syntax_queries.procedural import (
    classify_reset_style,
    enclosing_combinational_style_always_block,
    is_combinational_style_always_block,
    iter_assignment_nodes,
    iter_identifier_reads,
    missing_sensitivity_trigger_nodes,
    mixed_assignment_trigger_node,
    multiple_nonblocking_write_trigger_nodes,
    procedural_block_sensitivity_names,
)
from ._syntax_queries.shapes import (
    conditional_statement_body,
    conditional_statement_has_else,
    declarator_bit_width,
    declarator_has_initializer,
    declarator_is_parameter,
    declarator_is_port,
    declarator_is_signed,
    declarator_name,
    declarator_port_direction,
    else_clause_body,
    expression_statement_expression,
    has_full_parallel_case_pragma,
    has_timescale_directive_before,
    hierarchical_instance_list,
    hierarchical_instance_name,
    identifier_name,
    instantiation_type_name,
    is_block_statement,
    is_conditional_statement,
    is_else_clause_node,
    is_extra_module_declaration_in_file,
    is_first_module_declaration_in_file,
    is_missing_timescale_directive,
    is_module_declaration_node,
    is_named_parameter_override,
    is_ordered_parameter_override,
    is_parallel_block_statement,
    is_unlabeled_generate_block,
    is_unwrapped_else_body,
    is_unwrapped_if_body,
    iter_statement_nodes,
    named_parameter_override_name,
    named_port_connection_name,
    parameter_override_list,
    port_connection_expression,
    port_connection_list,
    procedural_block_statement,
)

from .syntax_kinds import (
    ALIAS_STATEMENT_KIND,
    ALWAYS_BLOCK_KIND,
    ALWAYS_COMB_BLOCK_KIND,
    ALWAYS_FF_BLOCK_KIND,
    ALWAYS_LATCH_BLOCK_KIND,
    ASSIGNMENT_KINDS,
    ASSIGN_DEASSIGN_TOKEN_KINDS,
    BIND_DIRECTIVE_KIND,
    CASE_STATEMENT_KIND,
    CASE_STYLE_TOKEN_KINDS,
    CASE_TOKEN_KINDS,
    CHANDLE_TYPE_KIND,
    CHECKER_DECLARATION_KIND,
    CLASS_DECLARATION_KIND,
    CLOCKING_DECLARATION_KIND,
    CONCURRENT_ASSERTION_KINDS,
    CONDITIONAL_STATEMENT_KIND,
    CONFIG_DECLARATION_KIND,
    CONTINUOUS_ASSIGN_KIND,
    COVERGROUP_DECLARATION_KIND,
    COVER_CROSS_KIND,
    DELAY_CONTROL_KINDS,
    DISABLE_IFF_KIND,
    DISABLE_STATEMENT_KIND,
    DISABLE_TOKEN_KIND,
    DO_TOKEN_KIND,
    DO_WHILE_STATEMENT_KIND,
    DEFPARAM_ASSIGNMENT_KIND,
    DEFPARAM_TOKEN_KIND,
    DPI_IMPORT_EXPORT_KINDS,
    ELSE_CLAUSE_KIND,
    ENDCASE_TOKEN_KIND,
    EVENT_TRIGGER_STATEMENT_KINDS,
    EVENT_TRIGGER_TOKEN_KINDS,
    EXPECT_RESTRICT_PROPERTY_KINDS,
    EXTENDS_CLAUSE_KIND,
    FOR_LOOP_STATEMENT_KIND,
    FOR_TOKEN_KIND,
    FOREACH_TOKEN_KIND,
    FINAL_BLOCK_KIND,
    FOREVER_TOKEN_KIND,
    FORCE_RELEASE_TOKEN_KINDS,
    FUNCTION_DECLARATION_KIND,
    FUNCTION_PROTOTYPE_KIND,
    GATE_PRIMITIVE_TOKEN_KINDS,
    IMMEDIATE_ASSERTION_KINDS,
    INITIAL_BLOCK_KIND,
    INTEGER_LITERAL_EXPRESSION_KIND,
    INTEGER_VECTOR_EXPRESSION_KIND,
    INTERFACE_DECLARATION_KIND,
    INSIDE_TOKEN_KIND,
    INVOCATION_EXPRESSION_KIND,
    LET_DECLARATION_KIND,
    LOOP_GENERATE_KIND,
    COMPILATION_UNIT_KIND,
    MODPORT_DECLARATION_KIND,
    MODULE_DECLARATION_KIND,
    NAMED_TYPE_KIND,
    PARALLEL_BLOCK_STATEMENT_KIND,
    PACKAGE_DECLARATION_KIND,
    PORT_DIRECTION_TOKEN_KINDS,
    PRIMITIVE_DECLARATION_KIND,
    PRIMITIVE_INSTANTIATION_KIND,
    PROGRAM_DECLARATION_KIND,
    PROCEDURAL_BLOCK_KINDS,
    PROPERTY_DECLARATION_KIND,
    QUEUE_DIMENSION_SPECIFIER_KIND,
    RANDSEQUENCE_STATEMENT_KIND,
    RANGE_DIMENSION_SPECIFIER_KIND,
    READ_WRITE_ASSIGNMENT_KINDS,
    READ_WRITE_UNARY_KINDS,
    REAL_TYPE_KINDS,
    REPEAT_TOKEN_KIND,
    SIMPLE_ASSIGNMENT_KINDS,
    SCOPED_NAME_KIND,
    SEQUENCE_DECLARATION_KIND,
    SPECIFY_BLOCK_KIND,
    STRING_TYPE_KIND,
    SUPPLY0_SUPPLY1_TOKEN_KINDS,
    SWITCH_PRIMITIVE_TOKEN_KINDS,
    TASK_DECLARATION_KIND,
    TRANIF_RTRANIF_TOKEN_KINDS,
    TRAN_RTRAN_TOKEN_KINDS,
    TRIREG_TOKEN_KIND,
    UNIQUE0_TOKEN_KIND,
    UWIRE_TOKEN_KIND,
    VARIABLE_DIMENSION_KIND,
    VIRTUAL_INTERFACE_TYPE_KIND,
    WAIT_TOKEN_KIND,
    WHILE_TOKEN_KIND,
    WAND_WOR_TOKEN_KINDS,
    WILDCARD_DIMENSION_SPECIFIER_KIND,
    UNIQUE_PRIORITY_TOKEN_KINDS,
)
from .types import (
    CaseGenerateNode,
    CaseStatementNode,
    DefaultCaseItemNode,
    IDENTIFIER_NAME_NODE_TYPES,
    IdentifierNameNode,
    IdentifierSelectNameNode,
    IfGenerateNode,
    LoopGenerateNode,
    PortDeclarationNode,
    ProceduralBlockNode,
    SyntaxNode,
    SyntaxTree,
    SystemNameNode,
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


def is_function_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == FUNCTION_DECLARATION_KIND


def is_class_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == CLASS_DECLARATION_KIND


def is_covergroup_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == COVERGROUP_DECLARATION_KIND


def is_sequence_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == SEQUENCE_DECLARATION_KIND


def is_property_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == PROPERTY_DECLARATION_KIND


def is_let_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == LET_DECLARATION_KIND


def is_config_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == CONFIG_DECLARATION_KIND


def is_randsequence_statement_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == RANDSEQUENCE_STATEMENT_KIND


def is_expect_restrict_property_node(raw: object) -> bool:
    return getattr(raw, "kind", None) in EXPECT_RESTRICT_PROPERTY_KINDS


def is_virtual_interface_type_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == VIRTUAL_INTERFACE_TYPE_KIND


def is_dpi_import_export_node(raw: object) -> bool:
    return getattr(raw, "kind", None) in DPI_IMPORT_EXPORT_KINDS


def is_real_type_node(raw: object) -> bool:
    return getattr(raw, "kind", None) in REAL_TYPE_KINDS


def is_string_type_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == STRING_TYPE_KIND


def is_chandle_type_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == CHANDLE_TYPE_KIND


def is_dynamic_array_dimension_node(raw: object) -> bool:
    """True for a bare `[]` dimension (`int arr[];`) -- a dynamic array. The same
    `VariableDimensionSyntax` node is used for every unpacked dimension form; a
    dynamic array is the one with no `specifier` child at all (contrast a fixed
    size `[4]`, a range `[3:0]`, a queue `[$]`, or an associative index `[string]`,
    all of which populate `specifier`)."""
    return getattr(raw, "kind", None) == VARIABLE_DIMENSION_KIND and getattr(raw, "specifier", None) is None


def is_queue_dimension_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == QUEUE_DIMENSION_SPECIFIER_KIND


def is_associative_array_dimension_node(raw: object) -> bool:
    """True for an associative-array dimension: a wildcard index (`arr[*]`), or an
    explicit built-in-type index (`arr[string]`, `arr[int]`, `arr[byte]`, ...).

    A user-defined-type index (`arr[my_type_t]`) is deliberately NOT recognized:
    it parses as an ordinary `IdentifierNameSyntax` under the same
    `RangeDimensionSpecifier` -> `BitSelect` shape as a perfectly ordinary
    parameter-sized fixed array (`arr[WIDTH]`), and telling the two apart needs
    type/symbol resolution this syntax-only check doesn't have -- guessing would
    misfire on completely ordinary, rule-compliant RTL. `sl.DataTypeSyntax` is the
    real discriminator for the recognized cases: a dimension index is always an
    expression syntactically, so a genuine type-keyword node there (`KeywordTypeSyntax`
    for `string`, `IntegerTypeSyntax` for `int`/`byte`/`bit`/...) is unambiguous.
    """
    kind = getattr(raw, "kind", None)
    if kind == WILDCARD_DIMENSION_SPECIFIER_KIND:
        return True
    if kind != RANGE_DIMENSION_SPECIFIER_KIND:
        return False
    selector = getattr(raw, "selector", None)
    index_expr = getattr(selector, "expr", None)
    return isinstance(index_expr, sl.DataTypeSyntax)


def is_program_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == PROGRAM_DECLARATION_KIND


def is_package_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == PACKAGE_DECLARATION_KIND


def is_specify_block_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == SPECIFY_BLOCK_KIND


def is_primitive_declaration_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == PRIMITIVE_DECLARATION_KIND


def is_alias_statement_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == ALIAS_STATEMENT_KIND


def is_bind_directive_node(raw: object) -> bool:
    return getattr(raw, "kind", None) == BIND_DIRECTIVE_KIND


def is_bind_directive_target(raw: object) -> bool:
    """True if `raw` is the target-module-name identifier of a `bind` directive.

    That identifier names a module/scope, not a variable, so it must not be treated
    as an ordinary identifier read (which would otherwise register it as an implicit net).
    """
    parent = getattr(raw, "parent", None)
    if getattr(parent, "kind", None) != BIND_DIRECTIVE_KIND:
        return False
    return getattr(parent, "target", None) is raw


def is_subroutine_prototype_name(raw: object) -> bool:
    """True if `raw` is the declared name of a task/function prototype
    (`FunctionPrototypeSyntax.name`, shared by both `TaskDeclarationSyntax` and
    `FunctionDeclarationSyntax` -- pyslang uses one prototype node for both).

    That identifier declares the subroutine's name, not a variable read, so it must
    not be treated as an ordinary identifier reference (which would otherwise
    register it as an implicit net).
    """
    parent = getattr(raw, "parent", None)
    if getattr(parent, "kind", None) != FUNCTION_PROTOTYPE_KIND:
        return False
    return getattr(parent, "name", None) is raw


def _is_scoped_name_target(raw: object, owner_kind: object, field: str = "name") -> bool:
    """Walk up through any chain of `ScopedNameSyntax` segments (`a.b.c`) from `raw`
    and return True if the outermost segment is the `field` field of a node whose
    kind is `owner_kind`. Shared by defparam-target and similar hierarchical-path
    checks below. `field` defaults to `"name"`, the common case; pass e.g.
    `field="left"` for owners (like `InvocationExpressionSyntax`) that use a
    different field name for the name/path in this position."""
    node = getattr(raw, "parent", None)
    while node is not None and getattr(node, "kind", None) == SCOPED_NAME_KIND:
        parent = getattr(node, "parent", None)
        if getattr(parent, "kind", None) == owner_kind and getattr(parent, field, None) is node:
            return True
        node = parent
    return getattr(node, "kind", None) == owner_kind and getattr(node, field, None) is raw


def is_defparam_target(raw: object) -> bool:
    """True if `raw` is (or is a `ScopedNameSyntax` segment of) the hierarchical
    target of a `defparam` assignment (`defparam a.b.c = ...;`).

    That identifier chain names a hierarchical parameter-override path, not a
    variable read, so it must not be treated as an ordinary identifier reference
    (which would otherwise register the trailing segment as an implicit net).
    """
    return _is_scoped_name_target(raw, DEFPARAM_ASSIGNMENT_KIND)


def is_disable_statement_target(raw: object) -> bool:
    """True if `raw` is (or is a `ScopedNameSyntax` segment of) the block/task
    label named by a `disable` statement (`disable blk;` / `disable pkg::blk;`).

    That identifier names a structural label, not a variable read, so it must not
    be treated as an ordinary identifier reference.
    """
    return _is_scoped_name_target(raw, DISABLE_STATEMENT_KIND)


def is_named_type_reference(raw: object) -> bool:
    """True if `raw` is (or is a `ScopedNameSyntax` segment of) the type name in a
    `NamedTypeSyntax` (a plain typedef'd type `my_t v;`, or a package-scoped type
    `pkg::my_t v;`).

    That identifier names a type, not a variable, so it must not be treated as an
    ordinary identifier reference -- unlike the other structural-name cases here,
    this one is not gated behind any already-banned construct, so it can misfire
    on completely ordinary, rule-compliant RTL using a typedef.
    """
    return _is_scoped_name_target(raw, NAMED_TYPE_KIND)


def is_invocation_callee(raw: object) -> bool:
    """True if `raw` is (or is a `ScopedNameSyntax` segment of) the callee name of
    a function/task/`let` call (`InvocationExpressionSyntax.left`, e.g. `f(1, 2)`
    or `pkg::f(1, 2)`).

    That identifier names the thing being called, not a variable being read, so it
    must not be treated as an ordinary identifier reference. Companion to
    `is_subroutine_prototype_name`, which only covers the *declaration* name --
    without this, calling any subroutine (including a DPI import, which has no
    banning rule at all) produces a false implicit net at the call site.
    """
    return _is_scoped_name_target(raw, INVOCATION_EXPRESSION_KIND, field="left")


def is_cover_cross_item(raw: object) -> bool:
    """True if `raw` is one of the coverpoint-label arguments of a `cross`
    statement (`CoverCrossSyntax.items`, e.g. `cpx`/`cpy` in `crs: cross cpx, cpy;`).

    Those identifiers name previously-declared coverpoint labels, not variables.
    """
    return getattr(getattr(raw, "parent", None), "kind", None) == COVER_CROSS_KIND


def is_extends_clause_base_name(raw: object) -> bool:
    """True if `raw` is (or is a `ScopedNameSyntax` segment of) the base-class name
    in a class `extends` clause (`class C extends Base;` / `class C extends pkg::Base;`).

    That identifier names a class, not a variable.
    """
    return _is_scoped_name_target(raw, EXTENDS_CLAUSE_KIND, field="baseName")


def is_delay_control_node(raw: object) -> bool:
    return getattr(raw, "kind", None) in DELAY_CONTROL_KINDS


def is_immediate_assertion_node(raw: object) -> bool:
    return getattr(raw, "kind", None) in IMMEDIATE_ASSERTION_KINDS


def is_concurrent_assertion_node(raw: object) -> bool:
    return getattr(raw, "kind", None) in CONCURRENT_ASSERTION_KINDS


def is_case_statement(raw: object) -> bool:
    return isinstance(raw, CaseStatementNode) or getattr(raw, "kind", None) == CASE_STATEMENT_KIND


def case_statement_items(raw: object) -> list[SyntaxNode]:
    """Return the case-item nodes under a `CaseStatementSyntax`, or `[]` if the
    node has no recognizable item list."""
    items = getattr(raw, "items", None)
    if items is None:
        return []
    return [item for item in items if isinstance(item, SyntaxNode)]


def case_item_expressions(raw: object) -> list[SyntaxNode]:
    """Return the selector expressions for one case item, or `[]` when the item
    has no expression list (for example a `default` item)."""
    items = getattr(raw, "expressions", None)
    if items is None:
        return []
    return [item for item in items if isinstance(item, SyntaxNode)]


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


def is_disable_token(raw: object, ctx: "Context") -> bool:
    if getattr(raw, "kind", None) != DISABLE_TOKEN_KIND:
        return False
    # `disable iff (...)` (a property's clock/reset qualifier) reuses the same
    # DisableKeyword token as an ordinary `disable <label>;` statement, but is a
    # completely different grammatical construct (DisableIffSyntax, not
    # DisableStatementSyntax) -- not a disable statement at all.
    for ancestor in reversed(ctx.stack):
        if getattr(ancestor.raw, "kind", None) == DISABLE_IFF_KIND:
            return False
    return True


def is_do_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == DO_TOKEN_KIND


def is_event_trigger_token(raw: object, ctx: "Context") -> bool:
    if getattr(raw, "kind", None) not in EVENT_TRIGGER_TOKEN_KINDS:
        return False
    # `->` is also SystemVerilog's ordinary logical-implication operator, usable in
    # any expression (`a -> b`), not just an event-trigger statement (`-> done;`).
    # Both share TokenKind.MinusArrow; only the statement form is an event trigger.
    for ancestor in reversed(ctx.stack):
        if getattr(ancestor.raw, "kind", None) in EVENT_TRIGGER_STATEMENT_KINDS:
            return True
    return False


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


def is_unique0_if_token(raw: object, ctx: "Context") -> bool:
    if UNIQUE0_TOKEN_KIND is None or getattr(raw, "kind", None) != UNIQUE0_TOKEN_KIND:
        return False

    conditional_statement = enclosing_conditional_statement(ctx)
    if conditional_statement is None:
        return False

    return conditional_statement_unique_or_priority(conditional_statement.raw) == "unique0"


def is_defparam_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == DEFPARAM_TOKEN_KIND


def is_force_release_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in FORCE_RELEASE_TOKEN_KINDS


def is_assign_deassign_token(raw: object, ctx: "Context") -> bool:
    if getattr(raw, "kind", None) not in ASSIGN_DEASSIGN_TOKEN_KINDS:
        return False
    # `assign` also begins an ordinary continuous assignment (`assign x = y;`), which is
    # completely standard RTL, not the legacy procedural assign/deassign this rule targets.
    return enclosing_continuous_assign(ctx) is None


def is_wand_wor_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in WAND_WOR_TOKEN_KINDS


def is_trireg_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == TRIREG_TOKEN_KIND


def is_uwire_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == UWIRE_TOKEN_KIND


def is_supply0_supply1_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in SUPPLY0_SUPPLY1_TOKEN_KINDS


def is_tran_rtran_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in TRAN_RTRAN_TOKEN_KINDS


def is_tranif_rtranif_token(raw: object) -> bool:
    return getattr(raw, "kind", None) in TRANIF_RTRANIF_TOKEN_KINDS


def is_gate_primitive_token(raw: object, ctx: "Context") -> bool:
    if getattr(raw, "kind", None) not in GATE_PRIMITIVE_TOKEN_KINDS:
        return False
    # `and`/`or`/`not`/... keywords are only gate-primitive types inside a
    # PrimitiveInstantiationSyntax. `TokenKind.OrKeyword` is also the separator in
    # classic event/sensitivity lists (`@(posedge clk or negedge rst_n)`), which is
    # a completely different, non-gate construct sharing the same token kind.
    return enclosing_primitive_instantiation(ctx) is not None


def is_switch_primitive_token(raw: object, ctx: "Context") -> bool:
    """Companion to `is_gate_primitive_token` for the switch-level primitives
    (`cmos`/`nmos`/`pmos`/`rcmos`/`rnmos`/`rpmos`/`pullup`/`pulldown`) that
    `NO_GATE_PRIMITIVE` explicitly left out of its first pass. Same context-gating
    rationale: these keywords only name a switch primitive inside a
    `PrimitiveInstantiationSyntax`."""
    if getattr(raw, "kind", None) not in SWITCH_PRIMITIVE_TOKEN_KINDS:
        return False
    return enclosing_primitive_instantiation(ctx) is not None


def is_endcase_token(raw: object) -> bool:
    return getattr(raw, "kind", None) == ENDCASE_TOKEN_KIND


def is_case_generate_keyword_pair(raw: object) -> bool:
    return str(getattr(raw, "keyword", "")).strip() == "case" and str(getattr(raw, "endCase", "")).strip() == "endcase"


def has_default_case_item(raw: object) -> bool:
    items = getattr(raw, "items", [])
    return any(isinstance(item, DefaultCaseItemNode) for item in items)


def is_posedge_event(raw: object) -> bool:
    return str(getattr(raw, "edge", "")).strip() == "posedge"


def is_negedge_event(raw: object) -> bool:
    return str(getattr(raw, "edge", "")).strip() == "negedge"


def module_declaration_name(raw: object) -> str | None:
    header = getattr(raw, "header", None)
    name = getattr(header, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def module_declaration_names_in_file(tree: SyntaxTree) -> list[str]:
    root = tree.root
    names: list[str] = []
    if getattr(root, "kind", None) == COMPILATION_UNIT_KIND:
        for member in getattr(root, "members", None) or []:
            if getattr(member, "kind", None) != MODULE_DECLARATION_KIND:
                continue
            name = module_declaration_name(member)
            if name:
                names.append(name)
        return names
    if is_module_declaration_node(root):
        name = module_declaration_name(root)
        if name:
            names.append(name)
    return names


def module_declaration_file_stem(current_file: str | None) -> str | None:
    if not current_file:
        return None
    return PurePath(current_file).stem


def is_module_filename_mismatch(raw: object, tree: SyntaxTree, current_file: str | None) -> bool:
    if not is_first_module_declaration_in_file(raw, tree):
        return False
    stem = module_declaration_file_stem(current_file)
    if not stem:
        return False
    return stem not in module_declaration_names_in_file(tree)


def primitive_declaration_name(raw: object) -> str | None:
    name = getattr(raw, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


DISPLAY_SYSTEM_TASK_NAMES = {
    "$display", "$displayb", "$displayh", "$displayo",
    "$write", "$writeb", "$writeh", "$writeo",
    "$monitor", "$monitorb", "$monitorh", "$monitoro",
    "$strobe", "$strobeb", "$strobeh", "$strobeo",
}

SIMULATION_CONTROL_TASK_NAMES = {"$stop", "$finish"}

RANDOM_SYSTEM_FUNCTION_NAMES = {"$random", "$urandom", "$urandom_range"}

TIME_SYSTEM_FUNCTION_NAMES = {"$time", "$realtime", "$stime"}

VCD_DUMP_TASK_NAMES = {
    "$dumpfile", "$dumpvars", "$dumpon", "$dumpoff", "$dumpall", "$dumpflush", "$dumplimit",
}

FILE_IO_SYSTEM_TASK_NAMES = {
    "$fopen", "$fclose",
    "$fdisplay", "$fdisplayb", "$fdisplayh", "$fdisplayo",
    "$fwrite", "$fwriteb", "$fwriteh", "$fwriteo",
    "$fstrobe", "$fstrobeb", "$fstrobeh", "$fstrobeo",
    "$fmonitor", "$fmonitorb", "$fmonitorh", "$fmonitoro",
    "$fscanf", "$fgets", "$fgetc", "$fread",
    "$fflush", "$feof", "$ferror", "$ftell", "$fseek", "$rewind", "$ungetc",
}

PLUSARGS_SYSTEM_FUNCTION_NAMES = {"$test$plusargs", "$value$plusargs"}

ASSERTION_CONTROL_TASK_NAMES = {
    "$assertoff", "$asserton", "$assertkill", "$assertcontrol",
    "$assertpasson", "$assertpassoff", "$assertfailon", "$assertfailoff",
    "$assertnonvacuouson", "$assertvacuousoff",
}


def system_task_name(raw: object) -> str | None:
    if not isinstance(raw, SystemNameNode):
        return None
    identifier = getattr(raw, "systemIdentifier", None)
    value = getattr(identifier, "valueText", None)
    return value if isinstance(value, str) and value else None


def is_display_system_task(raw: object) -> bool:
    return system_task_name(raw) in DISPLAY_SYSTEM_TASK_NAMES


def is_simulation_control_task(raw: object) -> bool:
    return system_task_name(raw) in SIMULATION_CONTROL_TASK_NAMES


def is_random_system_function(raw: object) -> bool:
    return system_task_name(raw) in RANDOM_SYSTEM_FUNCTION_NAMES


def is_time_system_function(raw: object) -> bool:
    return system_task_name(raw) in TIME_SYSTEM_FUNCTION_NAMES


def is_vcd_dump_task(raw: object) -> bool:
    return system_task_name(raw) in VCD_DUMP_TASK_NAMES


def is_file_io_system_task(raw: object) -> bool:
    return system_task_name(raw) in FILE_IO_SYSTEM_TASK_NAMES


def is_plusargs_system_function(raw: object) -> bool:
    return system_task_name(raw) in PLUSARGS_SYSTEM_FUNCTION_NAMES


def is_assertion_control_task(raw: object) -> bool:
    return system_task_name(raw) in ASSERTION_CONTROL_TASK_NAMES


__all__ = [
    "assignment_left",
    "assignment_right",
    "assignment_target_identifier_name",
    "case_statement_unique_or_priority",
    "classify_reset_style",
    "conditional_statement_unique_or_priority",
    "conditional_statement_body",
    "conditional_statement_has_else",
    "contains_descendant",
    "declarator_has_initializer",
    "declarator_is_parameter",
    "declarator_is_port",
    "declarator_name",
    "declarator_port_direction",
    "else_clause_body",
    "enclosing_case_statement",
    "enclosing_combinational_style_always_block",
    "enclosing_conditional_statement",
    "enclosing_continuous_assign",
    "enclosing_primitive_instantiation",
    "enclosing_procedural_block",
    "expression_statement_expression",
    "has_default_case_item",
    "has_full_parallel_case_pragma",
    "has_timescale_directive_before",
    "hierarchical_instance_name",
    "identifier_access_modes",
    "identifier_is_assignment_lhs",
    "identifier_name",
    "instantiation_type_name",
    "is_alias_statement_node",
    "is_always_comb_block",
    "is_always_ff_block",
    "is_always_latch_block",
    "is_assertion_control_task",
    "is_assign_deassign_token",
    "is_assignment_expression",
    "is_associative_array_dimension_node",
    "is_bind_directive_node",
    "is_bind_directive_target",
    "is_block_statement",
    "is_blocking_assignment_token",
    "is_combinational_driver_block",
    "is_case_generate_keyword_pair",
    "is_case_inside_token",
    "is_case_generate_node",
    "is_case_keyword_token",
    "is_case_statement",
    "is_casex_casez_token",
    "is_chandle_type_node",
    "is_checker_declaration_node",
    "is_class_declaration_node",
    "is_clocking_declaration_node",
    "is_combinational_style_always_block",
    "is_concurrent_assertion_node",
    "is_conditional_statement",
    "is_config_declaration_node",
    "is_continuous_assign",
    "is_covergroup_declaration_node",
    "is_cover_cross_item",
    "is_defparam_target",
    "is_delay_control_node",
    "is_disable_statement_target",
    "is_disable_token",
    "is_dpi_import_export_node",
    "is_dynamic_array_dimension_node",
    "is_else_clause_node",
    "is_extends_clause_base_name",
    "is_display_system_task",
    "is_do_token",
    "is_do_while_statement",
    "is_defparam_token",
    "is_endcase_token",
    "is_event_trigger_token",
    "is_expect_restrict_property_node",
    "is_extra_module_declaration_in_file",
    "is_file_io_system_task",
    "is_first_module_declaration_in_file",
    "is_for_token",
    "is_foreach_token",
    "is_final_block",
    "is_forever_token",
    "is_force_release_token",
    "is_function_declaration_node",
    "is_gate_primitive_token",
    "is_if_generate_node",
    "is_immediate_assertion_node",
    "is_initial_block",
    "is_interface_declaration_node",
    "is_missing_timescale_directive",
    "is_module_declaration_node",
    "is_inside_operator_token",
    "is_internal_inout_port_declaration",
    "is_invocation_callee",
    "is_let_declaration_node",
    "is_loop_generate_node",
    "is_modport_declaration_node",
    "is_named_parameter_override",
    "is_named_type_reference",
    "is_negedge_event",
    "is_ordered_parameter_override",
    "is_nonblocking_assignment_token",
    "is_parallel_block_statement",
    "is_plain_for_token",
    "is_posedge_event",
    "is_primitive_declaration_node",
    "is_priority_if_token",
    "is_package_declaration_node",
    "is_plusargs_system_function",
    "is_program_declaration_node",
    "is_plain_while_token",
    "is_procedural_block",
    "is_property_declaration_node",
    "is_queue_dimension_node",
    "is_randsequence_statement_node",
    "is_random_system_function",
    "is_read_write_assignment_expression",
    "is_read_write_unary_expression",
    "is_real_type_node",
    "is_repeat_token",
    "is_sequence_declaration_node",
    "is_simulation_control_task",
    "is_specify_block_node",
    "is_string_type_node",
    "is_subroutine_prototype_name",
    "is_supply0_supply1_token",
    "is_switch_primitive_token",
    "is_task_declaration_node",
    "is_time_system_function",
    "is_tranif_rtranif_token",
    "is_tran_rtran_token",
    "is_trireg_token",
    "is_unique0_case_token",
    "is_unique0_if_token",
    "is_unique_if_token",
    "is_unique_priority_case_token",
    "is_unlabeled_generate_block",
    "is_unsized_literal",
    "is_unsized_literal_in_flagged_value_context",
    "is_unwrapped_else_body",
    "is_unwrapped_if_body",
    "is_uwire_token",
    "is_vcd_dump_task",
    "is_virtual_interface_type_node",
    "is_wait_token",
    "is_while_token",
    "is_wand_wor_token",
    "iter_assignment_nodes",
    "iter_identifier_reads",
    "iter_statement_nodes",
    "mixed_assignment_trigger_node",
    "multiple_nonblocking_write_trigger_nodes",
    "missing_sensitivity_trigger_nodes",
    "module_declaration_name",
    "module_declaration_names_in_file",
    "module_declaration_file_stem",
    "is_module_filename_mismatch",
    "named_parameter_override_name",
    "parameter_override_list",
    "primitive_declaration_name",
    "procedural_block_sensitivity_names",
    "procedural_block_statement",
    "sized_literal_overflow",
    "source_text_for_node",
    "system_task_name",
    "unary_write_operand",
]
