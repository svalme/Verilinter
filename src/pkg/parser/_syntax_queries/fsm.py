"""State-register-shape primitives shared by the `fsms` rule category.

Deliberately scoped to the one-process FSM style only: a `case` statement
directly inside the clocked block whose selector is nonblocking-assigned in
that same block. The classic two-process style (a separate `always_comb`
next-state block feeding a plain `state <= next_state;` in the sequential
block) needs cross-block correlation this module doesn't attempt -- a known,
documented gap, consistent with why `UNREACHABLE_STATE`/`DEADLOCK_STATE`
aren't attempted at all yet.
"""

from ..syntax_kinds import NONBLOCKING_ASSIGNMENT_KIND
from .shared import identifier_name


def case_statement_selector_name(raw: object) -> str | None:
    """Return the selector identifier's name for a `CaseStatementSyntax`
    (`case (state) ...`), else `None` when the selector isn't a simple
    identifier."""
    return identifier_name(getattr(raw, "expr", None))


def is_state_register_case(raw: object, ctx: "Context") -> bool:
    """True if `raw` is a case statement whose selector is a simple
    identifier that is also a nonblocking-assignment target somewhere in the
    enclosing edge-sensitive (sync- or async-classified) procedural block --
    the classic one-process FSM shape:
    `always @(posedge clk) case (state) ... state <= next; ... endcase`.
    """
    from ..syntax_queries import (
        assignment_target_identifier_name,
        classify_reset_style,
        enclosing_procedural_block,
        is_case_statement,
        iter_assignment_nodes,
    )

    if not is_case_statement(raw):
        return False

    name = case_statement_selector_name(raw)
    if name is None:
        return False

    block = enclosing_procedural_block(ctx)
    if block is None or classify_reset_style(block.raw) not in ("sync", "async"):
        return False

    for node in iter_assignment_nodes(block.raw):
        if (
            getattr(node, "kind", None) == NONBLOCKING_ASSIGNMENT_KIND
            and assignment_target_identifier_name(node) == name
        ):
            return True
    return False


def resolve_case_item_value(expr: object, scope: object) -> int | None:
    """Best-effort resolve a case item's selector expression to a constant
    `int`: a simple identifier is looked up in `scope` for its `Symbol.value`
    (the common case -- a named state constant like `IDLE`); otherwise falls
    back to constant-folding the expression directly (a case item written as
    a bare literal instead of a named constant). Returns `None` when neither
    resolves.
    """
    from ..syntax_queries import constant_integer_value

    name = identifier_name(expr)
    if name is not None:
        lookup_fn = getattr(scope, "lookup_hierarchical", getattr(scope, "lookup", lambda _name: None))
        symbol = lookup_fn(name)
        value = getattr(symbol, "value", None)
        if isinstance(value, int):
            return value
        return None
    return constant_integer_value(expr)
