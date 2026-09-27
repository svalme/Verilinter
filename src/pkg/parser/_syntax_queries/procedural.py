from collections.abc import Iterator

from ..syntax_kinds import (
    ALWAYS_BLOCK_KIND,
    ALWAYS_FF_BLOCK_KIND,
    BLOCK_ITEM_SKIP_KINDS,
    CASE_ITEM_KINDS,
    CASE_STATEMENT_KIND,
    EVENT_CONTROL_OR_EXPRESSION_KINDS,
    EXPRESSION_STATEMENT_KIND,
    INVOCATION_EXPRESSION_KIND,
    NONBLOCKING_ASSIGNMENT_KIND,
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
    SyntaxTree,
)


def iter_identifier_reads(root: SyntaxNode) -> Iterator[tuple[str, SyntaxNode]]:
    """Yield (name, raw_node) for every read-access identifier under `root`, in document
    order. Does not descend into a nested procedural block."""

    from ..syntax_queries import identifier_name, is_identifier_name_node
    from .access import _identifier_access_modes_over_ancestors

    if not isinstance(root, SyntaxNode):
        return

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

    if not isinstance(root, SyntaxNode):
        return

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


def procedural_block_edge_events(raw: object) -> list[tuple[str, str]]:
    """Return all (edge_kind, signal_name) tuples for edge-qualified events
    in `raw`'s sensitivity list in document order.
    """
    from ..syntax_queries import is_negedge_event, is_posedge_event

    if getattr(raw, "kind", None) not in (ALWAYS_BLOCK_KIND, ALWAYS_FF_BLOCK_KIND):
        return []

    timing_statement = getattr(raw, "statement", None)
    if getattr(timing_statement, "kind", None) != TIMING_CONTROL_STATEMENT_KIND:
        return []

    event_control = getattr(timing_statement, "timingControl", None)
    if isinstance(event_control, ImplicitEventControlNode):
        return []

    events: list[tuple[str, str]] = []

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
                        events.append((edge, name))

    _walk(getattr(event_control, "expr", None))
    return events


def procedural_block_top_level_reset_names(raw: object) -> set[str]:
    """Return the set of signal names tested in the top-level `if` (and chained
    `else if`) condition predicates of procedural block `raw`.
    """
    from ..syntax_queries import is_block_statement, is_conditional_statement

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
            for name, _ in _iter_identifier_nodes(pred):
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
    from ..syntax_queries import (
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
    from ..types import SignalEventExpressionNode

    if not is_identifier_name_node(vnode.raw):
        return False

    name = identifier_name(vnode.raw)
    if not name:
        return False

    async_resets = ctx.data.get("module_async_resets")
    if not async_resets or name not in async_resets:
        return False

    # 1. Not flagged if it is a write (assignment LHS, e.g. assign rst_n = ~rst_in;)
    if identifier_is_assignment_lhs(ctx, vnode.raw):
        return False

    # 2. Not flagged if in a submodule port connection (passing reset down hierarchy)
    if enclosing_port_connection(ctx) is not None:
        return False

    # 3. Not flagged if in an event control or sensitivity list
    for ancestor in reversed(ctx.stack):
        raw = ancestor.raw
        if getattr(raw, "kind", None) in EVENT_CONTROL_OR_EXPRESSION_KINDS:
            return False

    # 4. Not flagged if in an assertion statement or diagnostic system task
    for ancestor in reversed(ctx.stack):
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

    if not isinstance(node, SyntaxNode):
        return

    if is_assignment_expression(node):
        yield node

    for child in node:
        if not isinstance(child, SyntaxNode):
            continue
        if isinstance(child, ProceduralBlockNode):
            continue
        yield from iter_assignment_nodes(child)


def mixed_assignment_trigger_node(block_raw: object) -> SyntaxNode | None:
    if not isinstance(block_raw, SyntaxNode):
        return None

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
    if not isinstance(node, SyntaxNode):
        return object()
    stmt = node
    depth = 0
    while stmt is not None and getattr(stmt, "kind", None) != EXPRESSION_STATEMENT_KIND and depth < 64:
        depth += 1
        stmt = getattr(stmt, "parent", None)
    if stmt is None or depth >= 64:
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
    if not isinstance(block_raw, SyntaxNode):
        return {}

    from .access import assignment_target_identifier_name

    triggers: dict[str, SyntaxNode] = {}
    seen_parents_by_target: dict[str, list[object]] = {}

    for node in iter_assignment_nodes(block_raw):
        if getattr(node, "kind", None) not in SIMPLE_ASSIGNMENT_KINDS:
            continue
        if getattr(node, "kind", None) != NONBLOCKING_ASSIGNMENT_KIND:
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


BranchSignature = tuple[tuple[str, int], ...]


def _construct_identity(construct: object, tree: SyntaxTree | None = None) -> str:
    """Return a deterministic string identity for an enclosing branching construct.

    Uses `file:line:col` via the syntax tree's sourceManager when available,
    falling back to buffer offset or object id if location cannot be resolved.
    """
    source_range = getattr(construct, "sourceRange", None)
    start = getattr(source_range, "start", None)
    if start is not None and tree is not None and getattr(tree, "sourceManager", None) is not None:
        sm = tree.sourceManager
        try:
            file_name = sm.getFileName(start)
            line = sm.getLineNumber(start)
            col = sm.getColumnNumber(start)
            return f"{file_name}:{line}:{col}"
        except Exception:
            pass
    if start is not None and hasattr(start, "offset"):
        return f"offset:{start.offset}"
    return f"id:{id(construct)}"


def construct_branch_metadata(
    construct: object, tree: SyntaxTree | None = None
) -> tuple[set[int] | None, BranchSignature]:
    """Return `(required_branches, parent_signature)` for a branching construct.

    For `if`/`else` (`ConditionalStatement`, `IfGenerate`):
        required_branches is `{0, 1}` if an `else` clause is present, else `None`.
    For `case` (`CaseStatement`, `CaseGenerate`):
        required_branches is `set(range(len(items)))` if a `default` case item or
        `unique`/`priority` qualifier is present, else `None`.
    """
    from ..syntax_kinds import DEFAULT_CASE_ITEM_KIND
    from ..syntax_queries import has_default_case_item, is_conditional_statement
    from .node_kind_checks import is_case_generate_node, is_if_generate_node

    parent_sig = branch_exclusivity_signature(construct, tree)

    if is_conditional_statement(construct) or is_if_generate_node(construct):
        else_clause = getattr(construct, "elseClause", None)
        required_branches = {0, 1} if else_clause is not None else None
        return required_branches, parent_sig

    if getattr(construct, "kind", None) == CASE_STATEMENT_KIND or is_case_generate_node(construct):
        items = getattr(construct, "items", ())
        has_default = has_default_case_item(construct) or any(
            getattr(it, "kind", None) == DEFAULT_CASE_ITEM_KIND for it in items
        )
        unique_or_priority = getattr(construct, "uniqueOrPriority", None)
        has_unique_priority = bool(unique_or_priority)
        required_branches = (
            set(range(len(items))) if ((has_default or has_unique_priority) and len(items) > 0) else None
        )
        return required_branches, parent_sig

    return None, parent_sig


def branch_exclusivity_signature(
    raw: object,
    tree: SyntaxTree | None = None,
    construct_registry: dict[str, tuple[set[int] | None, BranchSignature]] | None = None,
) -> BranchSignature:
    """Return `((construct_identity, branch_taken), ...)` for every enclosing
    conditional construct (procedural `if`/`else`, generate `if`/`else`,
    procedural `case`, or generate `case`, mixed freely in any nesting order)
    between `raw` and the module root, outermost last.

    Generalizes `_enclosing_statement_parent`'s sibling-vs-branch distinction from
    "one target written twice in one block" to "any two nodes anywhere, possibly in
    different blocks or different generate branches entirely" -- exactly what
    `is_mutually_exclusive_branch_pair` needs to tell a real simultaneous conflict
    (multiple drivers, a dependency cycle) from two mutually-exclusive alternatives
    that can never both apply, whether the choice is made at elaboration time
    (`generate if (PARAM) ... else ...`, `case generate`, e.g. choosing a multiplier implementation)
    or at runtime (`if (rst) ... else ...`, procedural `case (state) ... endcase`).

    An `else if` chain works out correctly without special-casing it: each
    `ConditionalStatement`/`IfGenerate` in the chain is its own construct with its
    own identity, so a deeper `else if`'s branches only share a construct identity
    (and only conflict) with siblings under that same link of the chain.

    Construct identities are location-based (`file:line:col` via `_construct_identity`),
    making signatures deterministic across independent syntax trees, multi-process
    workers, and persistent cache storage.
    """
    from ..syntax_queries import is_conditional_statement, is_else_clause_node
    from .node_kind_checks import is_case_generate_node, is_if_generate_node

    if not isinstance(raw, SyntaxNode):
        return ()

    signature: list[tuple[str, int]] = []
    construct_nodes: list[object] = []
    node = raw
    parent = getattr(node, "parent", None)
    depth = 0
    while parent is not None and depth < 64:
        depth += 1
        if is_else_clause_node(parent):
            construct = getattr(parent, "parent", None)
            if construct is not None:
                signature.append((_construct_identity(construct, tree), 1))
                construct_nodes.append(construct)
        elif is_conditional_statement(parent) or is_if_generate_node(parent):
            primary = getattr(parent, "statement", None)
            if primary is None:
                primary = getattr(parent, "block", None)
            if node is primary:
                signature.append((_construct_identity(parent, tree), 0))
                construct_nodes.append(parent)
        elif getattr(parent, "kind", None) in CASE_ITEM_KINDS:
            clause = getattr(parent, "clause", None)
            if node is clause:
                construct = getattr(parent, "parent", None)
                if construct is not None and (
                    getattr(construct, "kind", None) == CASE_STATEMENT_KIND or is_case_generate_node(construct)
                ):
                    items = getattr(construct, "items", ())
                    branch_idx = next((i for i, it in enumerate(items) if it is parent), -1)
                    if branch_idx >= 0:
                        signature.append((_construct_identity(construct, tree), branch_idx))
                        construct_nodes.append(construct)
        node = parent
        parent = getattr(parent, "parent", None)

    sig_tuple = tuple(signature)
    if construct_registry is not None:
        for i, (cid, _bidx) in enumerate(signature):
            if cid not in construct_registry:
                construct_node = construct_nodes[i]
                parent_sig = sig_tuple[i + 1:]
                req_branches, _ = construct_branch_metadata(construct_node, tree)
                construct_registry[cid] = (req_branches, parent_sig)

    return sig_tuple


def is_mutually_exclusive_branch_pair(sig_a: BranchSignature, sig_b: BranchSignature) -> bool:
    """True if `sig_a`/`sig_b` (each from `branch_exclusivity_signature`) share an
    enclosing `if`/`else` construct where they take different branches -- at most
    one of the two nodes they came from can ever execute or be elaborated, so a
    rule comparing them for a simultaneous conflict should treat the pair as safe
    rather than flag it. No shared construct at all is *not* exclusive: with no
    branching relationship between them, both can genuinely apply at once.
    """
    branch_by_construct = dict(sig_a)
    return any(
        construct_id in branch_by_construct and branch_by_construct[construct_id] != branch
        for construct_id, branch in sig_b
    )
