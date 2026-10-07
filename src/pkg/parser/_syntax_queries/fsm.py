"""Structural models for one-process and bounded two-process state machines."""

from dataclasses import dataclass

from ..syntax_kinds import NONBLOCKING_ASSIGNMENT_KIND, MODULE_DECLARATION_KIND, ALWAYS_COMB_BLOCK_KIND, CONDITIONAL_STATEMENT_KIND
from ..traversal_guard import ast_descendants_iter
from ..types import DeclaratorNode
from .declarators import declarator_name
from .shared import identifier_name
from .node_cache import MISSING, node_cache_get, node_cache_put


@dataclass(frozen=True)
class StateTransition:
    sources: tuple[int, ...]
    destination: int | None
    # Syntax is retained only for this file's analysis; it never enters stores.
    assignment: object
    guards: tuple[tuple[object, bool], ...]


@dataclass(frozen=True)
class FsmModel:
    state_name: str
    next_state_name: str | None
    sequential_block: object
    case_statement: object
    legal_states: frozenset[int]
    transitions: tuple[StateTransition, ...]
    reset_covered: bool


@dataclass(frozen=True)
class _MemberWriteSummary:
    member: object
    is_sequential: bool
    written_targets: frozenset[str]
    nonblocking_targets: frozenset[str]
    nonblocking_rhs_by_target: dict[str, frozenset[str]]


def _block_declarator_names(block_raw: object, module_cache: dict[object, object] | None) -> frozenset[str]:
    cached = node_cache_get(module_cache, "block_declarators", block_raw)
    if cached is not MISSING:
        return cached  # type: ignore[return-value]
    names = frozenset(
        name
        for node in ast_descendants_iter(block_raw)
        if isinstance(node, DeclaratorNode) and (name := declarator_name(node)) is not None
    )
    node_cache_put(module_cache, "block_declarators", block_raw, names)
    return names


def _module_member_write_summaries(
    module_raw: object,
    module_cache: dict[object, object] | None,
) -> tuple[_MemberWriteSummary, ...]:
    from ..syntax_queries import (
        assignment_right,
        assignment_target_identifier_name,
        classify_reset_style,
        iter_assignment_nodes,
    )

    cached = node_cache_get(module_cache, "module_fsm_index", module_raw)
    if cached is not MISSING:
        return cached  # type: ignore[return-value]

    summaries: list[_MemberWriteSummary] = []
    for member in getattr(module_raw, "members", ()):
        is_seq = classify_reset_style(member) in ("sync", "async")
        written: set[str] = set()
        nb_targets: set[str] = set()
        nb_rhs: dict[str, set[str]] = {}
        for a in iter_assignment_nodes(member):
            target = assignment_target_identifier_name(a)
            if target is None:
                continue
            written.add(target)
            if is_seq and getattr(a, "kind", None) == NONBLOCKING_ASSIGNMENT_KIND:
                nb_targets.add(target)
                rhs_id = identifier_name(assignment_right(a))
                if rhs_id is not None:
                    nb_rhs.setdefault(target, set()).add(rhs_id)
        if written:
            summaries.append(
                _MemberWriteSummary(
                    member=member,
                    is_sequential=is_seq,
                    written_targets=frozenset(written),
                    nonblocking_targets=frozenset(nb_targets),
                    nonblocking_rhs_by_target={k: frozenset(v) for k, v in nb_rhs.items()},
                )
            )

    result = tuple(summaries)
    node_cache_put(module_cache, "module_fsm_index", module_raw, result)
    return result


def state_machine_model(raw: object, ctx: "Context") -> FsmModel | None:
    """Correlate a state case with one unambiguous sequential writer.

    Two-process recognition requires a direct ``state <= next_state`` link
    and a combinational case that writes that next-state variable. Searches
    stay within the current lexical container, excluding nested generate and
    subroutine scopes rather than guessing across them.
    """
    from ..syntax_queries import (
        assignment_target_identifier_name, assignment_right,
        classify_reset_style, enclosing_procedural_block,
        is_case_statement, is_combinational_style_always_block,
        iter_assignment_nodes, case_statement_items, case_item_expressions,
        is_state_register_reset_covered,
    )
    if not is_case_statement(raw):
        return None

    ctx_data = getattr(ctx, "data", None)
    module_cache: dict[object, object] | None = None
    if isinstance(ctx_data, dict):
        cached_fsm = ctx_data.get("fsm_model")
        if isinstance(cached_fsm, tuple) and len(cached_fsm) == 2 and cached_fsm[0] is raw:
            return cached_fsm[1]
        raw_cache = ctx_data.get("module_cache")
        if isinstance(raw_cache, dict):
            module_cache = raw_cache
            cached_model = node_cache_get(module_cache, "fsm_model", raw)
            if cached_model is not MISSING:
                return cached_model  # type: ignore[return-value]

    def _finish(model: FsmModel | None) -> FsmModel | None:
        node_cache_put(module_cache, "fsm_model", raw, model)
        return model

    state = case_statement_selector_name(raw)
    block = enclosing_procedural_block(ctx)
    if state is None or block is None:
        return _finish(None)
    sequential = None
    next_state = None
    if classify_reset_style(block.raw) in ("sync", "async"):
        if not any(getattr(a, "kind", None) == NONBLOCKING_ASSIGNMENT_KIND and
                   assignment_target_identifier_name(a) == state
                   for a in iter_assignment_nodes(block.raw)):
            return _finish(None)
        sequential = block.raw
    elif getattr(block.raw, "kind", None) == ALWAYS_COMB_BLOCK_KIND or is_combinational_style_always_block(block.raw):
        module = next((n.raw for n in reversed(ctx.stack)
                       if getattr(n.raw, "kind", None) == MODULE_DECLARATION_KIND), None)
        # Direct sibling blocks only; generate-local and function-local
        # symbols must not be conflated with identically named module nets.
        if module is None or block.raw.parent != module:
            return _finish(None)
        comb_decls = _block_declarator_names(block.raw, module_cache)
        if state in comb_decls:
            return _finish(None)
        state_symbol = ctx.scope().lookup_hierarchical(state)
        if state_symbol is None or getattr(getattr(state_symbol, "scope", None), "kind", None) != "module":
            return _finish(None)
        summaries = _module_member_write_summaries(module, module_cache)
        writers = [s for s in summaries if s.is_sequential and state in s.nonblocking_targets]
        if len(writers) != 1:
            return _finish(None)
        seq_summary = writers[0]
        sequential = seq_summary.member
        candidates = set(seq_summary.nonblocking_rhs_by_target.get(state, ()))
        written = {assignment_target_identifier_name(a) for a in iter_assignment_nodes(raw)}
        if state in written:
            return _finish(None)
        candidates &= written
        if len(candidates) != 1:
            return _finish(None)
        next_state = candidates.pop()
        if next_state == state:
            return _finish(None)
        seq_decls = _block_declarator_names(sequential, module_cache)
        if next_state in comb_decls or state in seq_decls or next_state in seq_decls:
            return _finish(None)
        next_symbol = ctx.scope().lookup_hierarchical(next_state)
        if next_symbol is None or getattr(next_symbol, "scope", None) is not state_symbol.scope:
            return _finish(None)
        # A second procedural writer makes the next-state relation ambiguous.
        for s in summaries:
            if s.member != sequential and state in s.written_targets:
                return _finish(None)
            if s.member != block.raw and next_state in s.written_targets:
                return _finish(None)
    else:
        return _finish(None)

    values = set()
    transitions = []
    destination_name = next_state or state
    for item in case_statement_items(raw):
        sources = tuple(v for expr in case_item_expressions(item)
                        if (v := resolve_case_item_value(expr, ctx.scope())) is not None)
        values.update(sources)
        for assignment in iter_assignment_nodes(item):
            if assignment_target_identifier_name(assignment) == destination_name:
                rhs = assignment_right(assignment)
                destination = resolve_case_item_value(rhs, ctx.scope())
                guards = []
                child = assignment
                for _ in range(128):
                    parent = getattr(child, "parent", None)
                    if parent is None or parent == item:
                        break
                    if getattr(parent, "kind", None) == CONDITIONAL_STATEMENT_KIND:
                        guards.append((getattr(parent, "predicate", None), getattr(parent, "statement", None) == child))
                    child = parent
                transitions.append(StateTransition(sources, destination, assignment, tuple(reversed(guards))))
    return _finish(
        FsmModel(
            state,
            next_state,
            sequential,
            raw,
            frozenset(values),
            tuple(transitions),
            is_state_register_reset_covered(sequential, state),
        )
    )


def case_statement_selector_name(raw: object) -> str | None:
    """Return the selector identifier's name for a `CaseStatementSyntax`
    (`case (state) ...`), else `None` when the selector isn't a simple
    identifier."""
    return identifier_name(getattr(raw, "expr", None))


def is_state_register_case(raw: object, ctx: "Context") -> bool:
    """True when the shared model establishes a supported state-register case."""
    return state_machine_model(raw, ctx) is not None


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
