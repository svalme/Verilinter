from collections.abc import Iterator

from ..syntax_kinds import (
    ALWAYS_BLOCK_KIND,
    ALWAYS_FF_BLOCK_KIND,
    SIMPLE_ASSIGNMENT_KINDS,
    TIMING_CONTROL_STATEMENT_KIND,
)
from ..types import (
    BinaryEventExpressionNode,
    ImplicitEventControlNode,
    ParenthesizedEventExpressionNode,
    ProceduralBlockNode,
    SignalEventExpressionNode,
    SyntaxNode,
)


def iter_identifier_reads(root: SyntaxNode) -> Iterator[tuple[str, SyntaxNode]]:
    """Yield (name, raw_node) for every read-access identifier under `root`, in document
    order. Does not descend into a nested procedural block."""

    from ..syntax_queries import identifier_name, is_identifier_name_node
    from .access import _identifier_access_modes_over_ancestors

    def _walk(node: SyntaxNode, ancestors: list[object]) -> Iterator[tuple[str, SyntaxNode]]:
        if is_identifier_name_node(node):
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
    from ..syntax_queries import identifier_name, is_identifier_name_node

    if is_identifier_name_node(root):
        name = identifier_name(root)
        if name:
            yield name, root

    for child in root:
        if isinstance(child, SyntaxNode):
            yield from _iter_identifier_nodes(child)


def _collect_sensitivity_events(node: object) -> tuple[set[str], bool]:
    from ..syntax_queries import is_negedge_event, is_posedge_event

    names: set[str] = set()
    has_edge = False

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
                for name, _identifier in _iter_identifier_nodes(expr):
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


def _count_edge_qualified_signals(node: object) -> int:
    from ..syntax_queries import is_negedge_event, is_posedge_event

    count = 0

    def _walk(current: object) -> None:
        nonlocal count
        if current is None:
            return
        if isinstance(current, ParenthesizedEventExpressionNode):
            _walk(getattr(current, "expr", None))
        elif isinstance(current, BinaryEventExpressionNode):
            _walk(getattr(current, "left", None))
            _walk(getattr(current, "right", None))
        elif isinstance(current, SignalEventExpressionNode):
            if is_posedge_event(current) or is_negedge_event(current):
                count += 1

    _walk(node)
    return count


def classify_reset_style(raw: object) -> str | None:
    if getattr(raw, "kind", None) not in (ALWAYS_BLOCK_KIND, ALWAYS_FF_BLOCK_KIND):
        return None

    timing_statement = getattr(raw, "statement", None)
    if getattr(timing_statement, "kind", None) != TIMING_CONTROL_STATEMENT_KIND:
        return None

    event_control = getattr(timing_statement, "timingControl", None)
    if isinstance(event_control, ImplicitEventControlNode):
        return None

    edge_count = _count_edge_qualified_signals(getattr(event_control, "expr", None))
    if edge_count == 1:
        return "sync"
    if edge_count >= 2:
        return "async"
    return None


def _edge_qualified_signal_names(node: object) -> set[str]:
    from ..syntax_queries import is_negedge_event, is_posedge_event

    names: set[str] = set()

    def _walk(current: object) -> None:
        if current is None:
            return
        if isinstance(current, ParenthesizedEventExpressionNode):
            _walk(getattr(current, "expr", None))
        elif isinstance(current, BinaryEventExpressionNode):
            _walk(getattr(current, "left", None))
            _walk(getattr(current, "right", None))
        elif isinstance(current, SignalEventExpressionNode):
            if is_posedge_event(current) or is_negedge_event(current):
                expr = getattr(current, "expr", None)
                if isinstance(expr, SyntaxNode):
                    for name, _identifier in _iter_identifier_nodes(expr):
                        names.add(name)

    _walk(node)
    return names


def async_reset_signal_names(raw: object) -> set[str]:
    """Return the names of every edge-qualified signal in `raw`'s (an
    AlwaysBlock/AlwaysFFBlock) sensitivity list, when it classifies as an
    async-reset block (2+ edge-qualified signals, see `classify_reset_style`)
    -- else an empty set. A sync-reset block's reset signal isn't in the
    sensitivity list at all and has no structural marker distinguishing it
    from any other identifier, so it can't be identified this way -- see
    `ASYNC_RESET_XZ_VALUE`'s deliberately async-only scope.
    """
    if classify_reset_style(raw) != "async":
        return set()

    timing_statement = getattr(raw, "statement", None)
    if getattr(timing_statement, "kind", None) != TIMING_CONTROL_STATEMENT_KIND:
        return set()

    event_control = getattr(timing_statement, "timingControl", None)
    if isinstance(event_control, ImplicitEventControlNode):
        return set()

    return _edge_qualified_signal_names(getattr(event_control, "expr", None))


def sync_clock_signal_name(raw: object) -> str | None:
    """Return the sole edge-qualified signal name in `raw`'s (an
    AlwaysBlock/AlwaysFFBlock) sensitivity list, when it classifies as a
    sync block (exactly one edge-qualified signal -- unambiguously the clock,
    see `classify_reset_style`), else `None`. Deliberately does not attempt an
    async block (2+ edge-qualified signals) -- same "don't guess which one is
    the clock" restraint as `async_reset_signal_names`.
    """
    if classify_reset_style(raw) != "sync":
        return None

    timing_statement = getattr(raw, "statement", None)
    if getattr(timing_statement, "kind", None) != TIMING_CONTROL_STATEMENT_KIND:
        return None

    event_control = getattr(timing_statement, "timingControl", None)
    if isinstance(event_control, ImplicitEventControlNode):
        return None

    names = _edge_qualified_signal_names(getattr(event_control, "expr", None))
    return next(iter(names)) if len(names) == 1 else None


def async_reset_signal_edges(raw: object) -> dict[str, str]:
    """Async-block companion to `async_reset_signal_names` that keeps each
    edge-qualified signal's polarity (`"posedge"`/`"negedge"`) instead of
    discarding it into a flat set. Only populated when `classify_reset_style`
    is `"async"` -- same async-only scope as `async_reset_signal_names`, used
    by `RESET_SIGNAL_NAMING` to check every edge-qualified name's suffix
    convention without needing to guess which one is "the reset".
    """
    from ..syntax_queries import is_negedge_event, is_posedge_event

    if classify_reset_style(raw) != "async":
        return {}

    timing_statement = getattr(raw, "statement", None)
    if getattr(timing_statement, "kind", None) != TIMING_CONTROL_STATEMENT_KIND:
        return {}

    event_control = getattr(timing_statement, "timingControl", None)
    if isinstance(event_control, ImplicitEventControlNode):
        return {}

    edges: dict[str, str] = {}

    def _walk(current: object) -> None:
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
                expr = getattr(current, "expr", None)
                if isinstance(expr, SyntaxNode):
                    for name, _identifier in _iter_identifier_nodes(expr):
                        edges[name] = edge

    _walk(getattr(event_control, "expr", None))
    return edges


def procedural_nesting_depth(ctx: "Context") -> int:
    """Count block/conditional/case-statement ancestors above the current
    position, back to (but not including) the nearest enclosing procedural
    block. The current node itself (the last entry of `ctx.stack`) is
    excluded -- callers add 1 back in for it. Loop statements are
    deliberately not counted -- `DEEPLY_NESTED_BLOCK` only tracks begin/end
    and if/case nesting, not loop-body nesting.
    """
    from ..syntax_queries import is_block_statement, is_case_statement, is_conditional_statement, is_procedural_block

    depth = 0
    for ancestor in reversed(ctx.stack[:-1]):
        if is_procedural_block(ancestor.raw):
            break
        if is_block_statement(ancestor.raw) or is_conditional_statement(ancestor.raw) or is_case_statement(ancestor.raw):
            depth += 1
    return depth


def enclosing_combinational_style_always_block(ctx: "Context") -> "BaseVNode | None":
    for ancestor in reversed(ctx.stack):
        if is_combinational_style_always_block(ancestor.raw):
            return ancestor
    return None


def missing_sensitivity_trigger_nodes(block_raw: object) -> dict[str, SyntaxNode]:
    from ..syntax_queries import procedural_block_statement

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


def iter_assignment_nodes(node: SyntaxNode) -> Iterator[SyntaxNode]:
    from ..syntax_queries import is_assignment_expression

    if is_assignment_expression(node):
        yield node

    for child in node:
        if not isinstance(child, SyntaxNode):
            continue
        if isinstance(child, ProceduralBlockNode):
            continue
        yield from iter_assignment_nodes(child)


def mixed_assignment_trigger_node(block_raw: object) -> SyntaxNode | None:
    seen_kinds: set[object] = set()

    for node in iter_assignment_nodes(block_raw):
        if node.kind not in seen_kinds and seen_kinds:
            return node
        seen_kinds.add(node.kind)

    return None


def _enclosing_statement_parent(node: object) -> object:
    """Return the syntax parent of `node`'s nearest enclosing `ExpressionStatement`.

    Two nonblocking writes to the same target sharing this identity are direct
    siblings in the same straight-line statement list -- the second unconditionally
    overwrites the first, making the first dead. Two writes in different branches
    of the same `if`/`else`/`case` (or an unconditional default write followed by a
    *nested* conditional override, the standard "default assignment" idiom) get
    different parents here on purpose: `if`'s own body and its `ElseClause` are
    distinct nodes even though both hang off the same `ConditionalStatement`, and a
    conditionally-nested override's parent is the conditional, not the default
    write's own enclosing block. A node with no `ExpressionStatement` ancestor (shouldn't
    happen for an assignment used as a statement) gets a unique sentinel so it
    never spuriously matches another write.
    """
    stmt = node
    while stmt is not None and str(getattr(stmt, "kind", "")) != "SyntaxKind.ExpressionStatement":
        stmt = getattr(stmt, "parent", None)
    if stmt is None:
        return object()
    return getattr(stmt, "parent", None)


def multiple_nonblocking_write_trigger_nodes(block_raw: object) -> dict[str, SyntaxNode]:
    """Return {target_name: second_write_node} for targets written by two or more
    *direct-sibling* nonblocking assignments -- see `_enclosing_statement_parent`
    for exactly what "sibling" excludes (mutually exclusive branches, and the
    unconditional-default-then-nested-override idiom), both deliberately not
    flagged since only the sibling case is definitely dead code rather than
    ordinary, correct RTL control flow.
    """
    from .access import assignment_target_identifier_name

    triggers: dict[str, SyntaxNode] = {}
    seen_parents_by_target: dict[str, list[object]] = {}

    for node in iter_assignment_nodes(block_raw):
        if getattr(node, "kind", None) not in SIMPLE_ASSIGNMENT_KINDS:
            continue
        if str(getattr(node, "kind", "")) != "SyntaxKind.NonblockingAssignmentExpression":
            continue
        name = assignment_target_identifier_name(node)
        if name is None:
            continue

        parent = _enclosing_statement_parent(node)
        seen_parents = seen_parents_by_target.setdefault(name, [])
        if name not in triggers and any(parent is existing for existing in seen_parents):
            triggers[name] = node
        seen_parents.append(parent)

    return triggers
