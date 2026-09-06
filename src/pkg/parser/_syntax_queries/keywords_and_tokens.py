import re

import pyslang as sl

from ..syntax_kinds import (
    ASSIGN_DEASSIGN_TOKEN_KINDS,
    CASE_STATEMENT_KIND,
    CASE_STYLE_TOKEN_KINDS,
    CASE_TOKEN_KINDS,
    CONCURRENT_ASSERTION_KINDS,
    DEFPARAM_TOKEN_KIND,
    DELAY_CONTROL_KINDS,
    DISABLE_IFF_KIND,
    DISABLE_TOKEN_KIND,
    DO_TOKEN_KIND,
    DO_WHILE_STATEMENT_KIND,
    ENDCASE_TOKEN_KIND,
    EVENT_TRIGGER_STATEMENT_KINDS,
    EVENT_TRIGGER_TOKEN_KINDS,
    FORCE_RELEASE_TOKEN_KINDS,
    FOREACH_TOKEN_KIND,
    FOREVER_TOKEN_KIND,
    FOR_TOKEN_KIND,
    GATE_PRIMITIVE_TOKEN_KINDS,
    IMMEDIATE_ASSERTION_KINDS,
    INSIDE_TOKEN_KIND,
    REPEAT_TOKEN_KIND,
    SUPPLY0_SUPPLY1_TOKEN_KINDS,
    SWITCH_PRIMITIVE_TOKEN_KINDS,
    TRANIF_RTRANIF_TOKEN_KINDS,
    TRAN_RTRAN_TOKEN_KINDS,
    TRIREG_TOKEN_KIND,
    UNIQUE0_TOKEN_KIND,
    UNIQUE_PRIORITY_TOKEN_KINDS,
    UWIRE_TOKEN_KIND,
    WAIT_TOKEN_KIND,
    WAND_WOR_TOKEN_KINDS,
    WHILE_TOKEN_KIND,
)
from ..types import CaseStatementNode, DefaultCaseItemNode, PortDeclarationNode, SyntaxNode, SyntaxTree


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
    from ..syntax_queries import is_loop_generate_node

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
    from ..syntax_queries import is_conditional_statement

    if not is_conditional_statement(raw):
        return None
    return _normalized_unique_or_priority(raw)


def is_unique_priority_case_token(raw: object, ctx: "Context") -> bool:
    from ..syntax_queries import enclosing_case_statement

    if getattr(raw, "kind", None) not in UNIQUE_PRIORITY_TOKEN_KINDS:
        return False

    case_statement = enclosing_case_statement(ctx)
    if case_statement is None:
        return False

    return case_statement_unique_or_priority(case_statement.raw) in {"unique", "priority"}


def is_unique0_case_token(raw: object, ctx: "Context") -> bool:
    from ..syntax_queries import enclosing_case_statement

    if UNIQUE0_TOKEN_KIND is None or getattr(raw, "kind", None) != UNIQUE0_TOKEN_KIND:
        return False

    case_statement = enclosing_case_statement(ctx)
    if case_statement is None:
        return False

    return case_statement_unique_or_priority(case_statement.raw) == "unique0"


def enclosing_conditional_statement(ctx: "Context") -> "BaseVNode | None":
    from ..syntax_queries import is_conditional_statement

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
    from ..syntax_queries import enclosing_continuous_assign

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
    from ..syntax_queries import enclosing_primitive_instantiation

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
    from ..syntax_queries import enclosing_primitive_instantiation

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
