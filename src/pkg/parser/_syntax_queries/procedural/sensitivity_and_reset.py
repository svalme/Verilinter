"""Sensitivity lists, edge events, clocks and resets of a procedural block, and the combinational or sequential style they decide."""
from __future__ import annotations

from ...syntax_kinds import (
    ALWAYS_BLOCK_KIND,
    ALWAYS_FF_BLOCK_KIND,
    BLOCK_ITEM_SKIP_KINDS,
    EVENT_CONTROL_OR_EXPRESSION_KINDS,
    INVOCATION_EXPRESSION_KIND,
    TIMING_CONTROL_STATEMENT_KIND,
)
from ...traversal_guard import guarded_traversal
from ...types import (
    BinaryEventExpressionNode,
    ImplicitEventControlNode,
    ParenthesizedEventExpressionNode,
    SignalEventExpressionNode,
    SyntaxNode,
)
from ..shared import identifier_name
from .blocks import iter_identifier_nodes, iter_identifier_reads


def _collect_sensitivity_events(node: object) -> tuple[set[str], bool]:
    from ...syntax_queries import is_negedge_event, is_posedge_event

    names: set[str] = set()
    has_edge = False

    @guarded_traversal(max_depth=64, default=None)
    def _collect(current: object) -> None:
        nonlocal has_edge
        if current is None:
            return
        if isinstance(current, ParenthesizedEventExpressionNode):
            _collect(getattr(current, "expr", None))
        elif isinstance(current, BinaryEventExpressionNode):
            _collect(getattr(current, "left", None))
            _collect(getattr(current, "right", None))
        elif isinstance(current, SignalEventExpressionNode):
            if is_posedge_event(current) or is_negedge_event(current):
                has_edge = True
            expr = getattr(current, "expr", None)
            if isinstance(expr, SyntaxNode):
                for name, _identifier in iter_identifier_nodes(expr):
                    names.add(name)

    _collect(node)
    return names, has_edge


def procedural_block_sensitivity_names(raw: object) -> set[str] | None:
    if getattr(raw, "kind", None) != ALWAYS_BLOCK_KIND:
        return None

    timing_statement = getattr(raw, "statement", None)
    if getattr(timing_statement, "kind", None) != TIMING_CONTROL_STATEMENT_KIND:
        return None

    event_control = getattr(timing_statement, "timingControl", None)
    if isinstance(event_control, ImplicitEventControlNode):
        return None

    names, has_edge = _collect_sensitivity_events(getattr(event_control, "expr", None))
    if has_edge:
        return None
    return names


def is_combinational_style_always_block(raw: object) -> bool:
    if getattr(raw, "kind", None) != ALWAYS_BLOCK_KIND:
        return False

    timing_statement = getattr(raw, "statement", None)
    if getattr(timing_statement, "kind", None) != TIMING_CONTROL_STATEMENT_KIND:
        return False

    event_control = getattr(timing_statement, "timingControl", None)
    if isinstance(event_control, ImplicitEventControlNode):
        return True

    _names, has_edge = _collect_sensitivity_events(getattr(event_control, "expr", None))
    return not has_edge


def is_sequential_style_procedural_block(raw: object) -> bool:
    if getattr(raw, "kind", None) == ALWAYS_FF_BLOCK_KIND:
        return True
    if getattr(raw, "kind", None) != ALWAYS_BLOCK_KIND:
        return False

    timing_statement = getattr(raw, "statement", None)
    if getattr(timing_statement, "kind", None) != TIMING_CONTROL_STATEMENT_KIND:
        return False

    event_control = getattr(timing_statement, "timingControl", None)
    if isinstance(event_control, ImplicitEventControlNode):
        return False

    _names, has_edge = _collect_sensitivity_events(getattr(event_control, "expr", None))
    return has_edge


def _inspect_edge_events(raw: object) -> tuple[int, list[tuple[str, str]]]:
    """Walk `raw`'s sensitivity-list event expression once, returning
    `(edge_clause_count, [(edge_kind, signal_name), ...])`.
    """
    from ...syntax_queries import is_negedge_event, is_posedge_event

    if getattr(raw, "kind", None) not in (ALWAYS_BLOCK_KIND, ALWAYS_FF_BLOCK_KIND):
        return 0, []

    timing_statement = getattr(raw, "statement", None)
    if getattr(timing_statement, "kind", None) != TIMING_CONTROL_STATEMENT_KIND:
        return 0, []

    event_control = getattr(timing_statement, "timingControl", None)
    if isinstance(event_control, ImplicitEventControlNode):
        return 0, []

    edge_count = 0
    events: list[tuple[str, str]] = []

    @guarded_traversal(max_depth=64, default=None)
    def _walk(current: object) -> None:
        nonlocal edge_count
        if current is None:
            return
        if isinstance(current, ParenthesizedEventExpressionNode):
            _walk(getattr(current, "expr", None))
        elif isinstance(current, BinaryEventExpressionNode):
            _walk(getattr(current, "left", None))
            _walk(getattr(current, "right", None))
        elif isinstance(current, SignalEventExpressionNode):
            if is_posedge_event(current):
                edge = "posedge"
            elif is_negedge_event(current):
                edge = "negedge"
            else:
                edge = None
            if edge is not None:
                edge_count += 1
                expr = getattr(current, "expr", None)
                if isinstance(expr, SyntaxNode):
                    for name, _identifier in iter_identifier_nodes(expr):
                        events.append((edge, name))

    _walk(getattr(event_control, "expr", None))
    return edge_count, events


def classify_reset_style(raw: object) -> str | None:
    edge_count, _events = _inspect_edge_events(raw)
    if edge_count == 1:
        return "sync"
    if edge_count >= 2:
        return "async"
    return None


def async_reset_signal_names(raw: object) -> set[str]:
    """Return the names of every edge-qualified signal in `raw`'s (an
    AlwaysBlock/AlwaysFFBlock) sensitivity list, when it classifies as an
    async-reset block (2+ edge-qualified signals, see `classify_reset_style`)
    -- else an empty set. A sync-reset block's reset signal isn't in the
    sensitivity list at all and has no structural marker distinguishing it
    from any other identifier, so it can't be identified this way -- see
    `ASYNC_RESET_XZ_VALUE`'s deliberately async-only scope.
    """
    edge_count, events = _inspect_edge_events(raw)
    if edge_count < 2:
        return set()
    return {name for _edge, name in events}


def sync_clock_signal_name(raw: object) -> str | None:
    """Return the sole edge-qualified signal name in `raw`'s (an
    AlwaysBlock/AlwaysFFBlock) sensitivity list, when it classifies as a
    sync block (exactly one edge-qualified signal -- unambiguously the clock,
    see `classify_reset_style`), else `None`. Deliberately does not attempt an
    async block (2+ edge-qualified signals) -- same "don't guess which one is
    the clock" restraint as `async_reset_signal_names`.
    """
    edge_count, events = _inspect_edge_events(raw)
    if edge_count != 1:
        return None
    names = {name for _edge, name in events}
    return next(iter(names)) if len(names) == 1 else None


def async_reset_signal_edges(raw: object) -> dict[str, str]:
    """Async-block companion to `async_reset_signal_names` that keeps each
    edge-qualified signal's polarity (`"posedge"`/`"negedge"`) instead of
    discarding it into a flat set. Only populated when `classify_reset_style`
    is `"async"` -- same async-only scope as `async_reset_signal_names`, used
    by `RESET_SIGNAL_NAMING` to check every edge-qualified name's suffix
    convention without needing to guess which one is "the reset".
    """
    edge_count, events = _inspect_edge_events(raw)
    if edge_count < 2:
        return {}
    return {name: edge for edge, name in events}


def procedural_block_edge_events(raw: object) -> list[tuple[str, str]]:
    """Return all (edge_kind, signal_name) tuples for edge-qualified events
    in `raw`'s sensitivity list in document order.
    """
    _edge_count, events = _inspect_edge_events(raw)
    return events


def procedural_block_top_level_reset_names(raw: object) -> set[str]:
    """Return the set of signal names tested in the top-level `if` (and chained
    `else if`) condition predicates of procedural block `raw`.
    """
    from ...syntax_queries import is_block_statement, is_conditional_statement

    if getattr(raw, "kind", None) not in (ALWAYS_BLOCK_KIND, ALWAYS_FF_BLOCK_KIND):
        return set()

    timing_statement = getattr(raw, "statement", None)
    if getattr(timing_statement, "kind", None) == TIMING_CONTROL_STATEMENT_KIND:
        stmt = getattr(timing_statement, "statement", None)
    else:
        stmt = timing_statement

    first_stmt = None
    if is_block_statement(stmt):
        items = getattr(stmt, "items", None)
        if items:
            for it in items:
                if getattr(it, "kind", None) in BLOCK_ITEM_SKIP_KINDS:
                    continue
                first_stmt = it
                break
    else:
        first_stmt = stmt

    reset_names: set[str] = set()
    curr = first_stmt
    depth = 0
    while is_conditional_statement(curr) and depth < 64:
        depth += 1
        pred = getattr(curr, "predicate", None)
        if isinstance(pred, SyntaxNode):
            for name, _ in iter_identifier_nodes(pred):
                reset_names.add(name)
        else_clause = getattr(curr, "elseClause", None)
        if else_clause is None:
            break
        clause_stmt = getattr(else_clause, "clause", None)
        if is_conditional_statement(clause_stmt):
            curr = clause_stmt
        else:
            break

    return reset_names


def is_multi_clock_procedural_block(raw: object) -> bool:
    """True if `raw` is a sequential procedural block whose sensitivity list
    contains multiple clock signals or illegal edge combinations (such as
    opposite edges of the same signal, multiple clock triggers, or multiple
    edge-qualified signals with no async reset condition).
    """
    events = procedural_block_edge_events(raw)
    if not events:
        return False

    edge_signals = [name for _edge, name in events]
    unique_signals = set(edge_signals)

    # If duplicate events on the same signal exist (e.g. posedge clk or negedge clk)
    if len(edge_signals) != len(unique_signals):
        return True

    # Single-edge block (e.g. always @(posedge clk)) is a valid synchronous clock
    if len(unique_signals) <= 1:
        return False

    # Block has 2 or more edge-qualified signals.
    # Exactly one can be the clock; the rest must be accounted for by the reset condition.
    reset_names = procedural_block_top_level_reset_names(raw)
    resets_in_edges = unique_signals & reset_names
    clocks = unique_signals - resets_in_edges

    # If more than 1 signal is not accounted for as a reset, multiple clocks exist!
    # If 0 signals act as a clock (all are in the reset condition), there is no clock trigger!
    return len(clocks) != 1


def procedural_block_async_reset_signals(raw: object) -> set[str]:
    """Return the set of signal names that serve as verified asynchronous resets
    in `raw` (an edge-qualified sequential block where 2+ edges exist, 1 is the clock,
    and the remaining edge-qualified signals are tested in the top-level reset condition).
    """
    events = procedural_block_edge_events(raw)
    if len(events) < 2:
        return set()

    edge_signals = [name for _edge, name in events]
    unique_signals = set(edge_signals)
    if len(edge_signals) != len(unique_signals):
        return set()

    reset_names = procedural_block_top_level_reset_names(raw)
    resets_in_edges = unique_signals & reset_names
    clocks = unique_signals - resets_in_edges
    if len(clocks) == 1 and len(resets_in_edges) >= 1:
        return resets_in_edges
    return set()


def module_async_reset_signals(module_raw: object) -> set[str]:
    """Return all verified asynchronous reset signal names across procedural blocks in `module_raw`."""
    members = getattr(module_raw, "members", None)
    if not members:
        return set()

    resets: set[str] = set()
    for member in members:
        kind = getattr(member, "kind", None)
        if kind in (ALWAYS_BLOCK_KIND, ALWAYS_FF_BLOCK_KIND):
            resets.update(procedural_block_async_reset_signals(member))
    return resets


def is_async_reset_read_as_data(vnode: "BaseVNode", ctx: "Context") -> bool:
    """True if `vnode` is an identifier reference reading an asynchronous reset
    signal as a data operand rather than in an event list, port connection,
    assertion, system task, or the top-level reset control predicate.
    """
    from ...syntax_queries import (
        contains_descendant,
        enclosing_port_connection,
        enclosing_procedural_block,
        identifier_is_assignment_lhs,
        identifier_name,
        is_block_statement,
        is_concurrent_assertion_node,
        is_conditional_statement,
        is_identifier_name_node,
        is_immediate_assertion_node,
        system_task_name,
    )
    from ...types import SignalEventExpressionNode

    if not is_identifier_name_node(vnode.raw):
        return False

    name = identifier_name(vnode.raw)
    if not name:
        return False

    module_frame = getattr(ctx, "module_frame", None)
    if module_frame is not None:
        async_resets = module_frame.async_reset_signals
    else:
        async_resets = ctx.data.get("module_async_resets") if hasattr(ctx, "data") else None
    if not async_resets or name not in async_resets:
        return False

    # 1. Not flagged if it is a write (assignment LHS, e.g. assign rst_n = ~rst_in;)
    if identifier_is_assignment_lhs(ctx, vnode.raw):
        return False

    # 2. Not flagged if in a submodule port connection (passing reset down hierarchy)
    if enclosing_port_connection(ctx) is not None:
        return False

    # 3. Not flagged if in an event control or sensitivity list
    for ancestor in ctx.iter_ancestors():
        raw = ancestor.raw
        if getattr(raw, "kind", None) in EVENT_CONTROL_OR_EXPRESSION_KINDS:
            return False

    # 4. Not flagged if in an assertion statement or diagnostic system task
    for ancestor in ctx.iter_ancestors():
        if is_immediate_assertion_node(ancestor.raw) or is_concurrent_assertion_node(ancestor.raw):
            return False
        if getattr(ancestor.raw, "kind", None) == INVOCATION_EXPRESSION_KIND:
            callee = getattr(ancestor.raw, "left", None)
            sys_name = system_task_name(callee) or identifier_name(callee) or ""
            if sys_name.startswith(("$display", "$monitor", "$strobe", "$write", "$info", "$warning", "$error", "$fatal")):
                return False

    # 5. Not flagged if in the predicate expression of a top-level async reset conditional
    block = enclosing_procedural_block(ctx)
    if block is not None:
        timing_statement = getattr(block.raw, "statement", None)
        if getattr(timing_statement, "kind", None) == TIMING_CONTROL_STATEMENT_KIND:
            inner_stmt = getattr(timing_statement, "statement", None)
        else:
            inner_stmt = timing_statement

        first_stmt = None
        if is_block_statement(inner_stmt):
            items = getattr(inner_stmt, "items", None)
            if items:
                for it in items:
                    if getattr(it, "kind", None) in BLOCK_ITEM_SKIP_KINDS:
                        continue
                    first_stmt = it
                    break
        else:
            first_stmt = inner_stmt

        curr = first_stmt
        depth = 0
        while is_conditional_statement(curr) and depth < 64:
            depth += 1
            pred = getattr(curr, "predicate", None)
            if pred is not None and contains_descendant(pred, vnode.raw):
                return False
            else_clause = getattr(curr, "elseClause", None)
            if else_clause is None:
                break
            clause_stmt = getattr(else_clause, "clause", None)
            if is_conditional_statement(clause_stmt):
                curr = clause_stmt
            else:
                break

    return True


def enclosing_combinational_style_always_block(ctx: "Context") -> "BaseVNode | None":
    block_frame = getattr(ctx, "block_frame", None)
    ctx_data = getattr(ctx, "data", None)
    cached = ctx_data.get("comb_always_block") if isinstance(ctx_data, dict) else None
    for ancestor in ctx.iter_ancestors():
        if block_frame is not None and block_frame.block_raw is ancestor.raw:
            if block_frame.is_comb:
                return ancestor
            continue
        if isinstance(cached, tuple) and len(cached) == 2 and cached[0] is ancestor.raw:
            if cached[1]:
                return ancestor
            continue
        if is_combinational_style_always_block(ancestor.raw):
            return ancestor
    return None


def missing_sensitivity_trigger_nodes(block_raw: object) -> dict[str, SyntaxNode]:
    from ...syntax_queries import procedural_block_statement

    sensitivity_names = procedural_block_sensitivity_names(block_raw)
    if sensitivity_names is None:
        return {}

    timing_statement = procedural_block_statement(block_raw)
    body = procedural_block_statement(timing_statement) if timing_statement is not None else None
    if body is None:
        return {}

    missing: dict[str, SyntaxNode] = {}
    for name, node in iter_identifier_reads(body):
        if name not in sensitivity_names and name not in missing:
            missing[name] = node
    return missing
