"""Assignments inside a procedural block and the branch each one sits in: which statement owns it, and whether two branches can both run."""
from __future__ import annotations

from collections.abc import Iterator
from ...syntax_kinds import CASE_ITEM_KINDS, CASE_STATEMENT_KIND, EXPRESSION_STATEMENT_KIND
from ...traversal_guard import guarded_generator
from ...types import ProceduralBlockNode, SyntaxNode, SyntaxTree
from ..shared import identifier_name, same_expression
from .blocks import node_syntax_children


BranchSignature = tuple[tuple[str, int], ...]


@guarded_generator(max_depth=128)
def iter_assignment_nodes(node: SyntaxNode) -> Iterator[SyntaxNode]:
    from ...syntax_queries import is_assignment_expression

    if not isinstance(node, SyntaxNode):
        return

    if is_assignment_expression(node):
        yield node

    for child in node_syntax_children(node):
        if isinstance(child, ProceduralBlockNode):
            continue
        yield from iter_assignment_nodes(child)


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


def _is_repeated_sibling_write(
    seen: list[tuple[object, object]], parent: object, target: object
) -> bool:
    """True when an earlier write in `seen` (statement parent, target expression) came from the same
    statement parent and wrote the same target. `a[0] <= x; a[1] <= y;` writes different parts of `a`."""
    return any(parent is earlier_parent and same_expression(target, earlier_target) for earlier_parent, earlier_target in seen)


def procedural_block_assignment_triggers(
    block_raw: object,
) -> tuple[SyntaxNode | None, dict[str, SyntaxNode]]:
    """Compute `(mixed_assignment_trigger_node, multiple_nonblocking_write_trigger_nodes)` for a block
    in a single `iter_assignment_nodes` pass.

    The mixed-style trigger is the first assignment whose blocking or non-blocking kind differs from the
    block's first assignment (a compound `x += y` is a blocking assignment). The repeated-write
    triggers are `{target_name: second_write_node}` for a target written by two *direct-sibling*
    non-blocking assignments to the same reference -- see `_enclosing_statement_parent` for exactly what
    "sibling" excludes (mutually exclusive branches, and the unconditional-default-then-nested-override
    idiom), both deliberately not flagged since only the sibling case is definitely dead code rather
    than ordinary, correct RTL control flow.
    """
    if not isinstance(block_raw, SyntaxNode):
        return None, {}

    from ....semantic.models.assignment_record import AssignmentKind
    from ..assignment_records import assignment_view

    mix_trigger: SyntaxNode | None = None
    first_is_nonblocking: bool | None = None
    nb_triggers: dict[str, SyntaxNode] = {}
    seen_targets_by_name: dict[str, list[tuple[object, object]]] = {}

    for node in iter_assignment_nodes(block_raw):
        view = assignment_view(node)
        if view is None:
            continue
        is_nonblocking = view.kind == AssignmentKind.NONBLOCKING
        if first_is_nonblocking is None:
            first_is_nonblocking = is_nonblocking
        elif mix_trigger is None and is_nonblocking != first_is_nonblocking:
            mix_trigger = node

        if not is_nonblocking:
            continue
        parent = _enclosing_statement_parent(node)
        for leaf in view.leaves:
            name = identifier_name(leaf)
            if name is None:
                continue
            seen = seen_targets_by_name.setdefault(name, [])
            if name not in nb_triggers and _is_repeated_sibling_write(seen, parent, leaf):
                nb_triggers[name] = node
            seen.append((parent, leaf))

    return mix_trigger, nb_triggers


def _construct_identity(construct: object, tree: SyntaxTree | None = None) -> str:
    """Return a deterministic string identity for an enclosing branching construct.

    Uses `file:line:col` via the syntax tree's sourceManager when available. A
    construct produced by a macro expansion reports line and column 0 of a
    per-expansion buffer, so it is identified by its outermost expansion site
    in the real file plus its offset inside the macro body: two expansions of
    one macro, even on the same line, get different identities. Without a
    resolvable location the object id is used, which cannot collide within the
    one process a tree-less caller runs in.
    """
    source_range = getattr(construct, "sourceRange", None)
    start = getattr(source_range, "start", None)
    if start is not None and tree is not None and getattr(tree, "sourceManager", None) is not None:
        sm = tree.sourceManager
        try:
            if sm.isMacroLoc(start):
                expanded = sm.getFullyExpandedLoc(start)
                original = sm.getFullyOriginalLoc(start)
                return (
                    f"{sm.getFileName(expanded)}:{sm.getLineNumber(expanded)}:"
                    f"{sm.getColumnNumber(expanded)}@{expanded.offset}+{original.offset}"
                )
            return f"{sm.getFileName(start)}:{sm.getLineNumber(start)}:{sm.getColumnNumber(start)}"
        except Exception:
            pass
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
    from ...syntax_kinds import DEFAULT_CASE_ITEM_KIND
    from ...syntax_queries import has_default_case_item, is_conditional_statement
    from ..node_kind_checks import is_case_generate_node, is_if_generate_node

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
    from ...syntax_queries import is_conditional_statement, is_else_clause_node
    from ..node_kind_checks import is_case_generate_node, is_if_generate_node

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
