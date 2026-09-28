from ..syntax_kinds import (
    ALWAYS_COMB_BLOCK_KIND,
    ELEMENT_SELECT_KIND,
    FOR_LOOP_STATEMENT_KIND,
    NONBLOCKING_ASSIGNMENT_KIND,
    PRIMITIVE_INSTANTIATION_KIND,
)
from ..traversal_guard import guarded_traversal
from ..types import ProceduralBlockNode, SyntaxNode
from .expressions import simple_expression_width_and_signed
from .shared import raw_node_children


@guarded_traversal(max_depth=64, default=False)
def contains_descendant(root: SyntaxNode, target: SyntaxNode) -> bool:
    if root is target:
        return True
    for child in raw_node_children(root):
        if isinstance(child, SyntaxNode) and contains_descendant(child, target):
            return True
    return False


def assignment_left(raw: object) -> SyntaxNode | None:
    from ..syntax_queries import is_assignment_expression

    if not is_assignment_expression(raw):
        return None
    left = getattr(raw, "left", None)
    return left if isinstance(left, SyntaxNode) else None


def binary_operands(raw: object) -> tuple[SyntaxNode, SyntaxNode] | None:
    """Return `(left, right)` for any binary-expression-shaped node -- shift,
    divide, and mod expressions all share this plain `.left`/`.right` shape --
    else `None`."""
    left = getattr(raw, "left", None)
    right = getattr(raw, "right", None)
    if isinstance(left, SyntaxNode) and isinstance(right, SyntaxNode):
        return left, right
    return None


def unary_write_operand(raw: object) -> SyntaxNode | None:
    from ..syntax_queries import is_read_write_unary_expression

    if not is_read_write_unary_expression(raw):
        return None
    operand = getattr(raw, "operand", None)
    return operand if isinstance(operand, SyntaxNode) else None


@guarded_traversal(max_depth=64, default=False)
def _selectors_containing_identifier(raw: object, raw_identifier: SyntaxNode) -> bool:
    if not isinstance(raw, SyntaxNode):
        return False

    selectors = getattr(raw, "selectors", None)
    if selectors is not None:
        for selector in selectors:
            if isinstance(selector, SyntaxNode) and contains_descendant(selector, raw_identifier):
                return True

    select = getattr(raw, "select", None)
    if select is not None and isinstance(select, SyntaxNode) and contains_descendant(select, raw_identifier):
        return True

    if getattr(raw, "kind", None) == ELEMENT_SELECT_KIND:
        return contains_descendant(raw, raw_identifier)

    for child in raw_node_children(raw):
        if isinstance(child, SyntaxNode) and contains_descendant(child, raw_identifier):
            if _selectors_containing_identifier(child, raw_identifier):
                return True

    return False


def _identifier_access_modes_over_ancestors(
    raw_ancestors: list[object], raw_identifier: SyntaxNode
) -> tuple[bool, bool]:
    from ..syntax_queries import is_read_write_assignment_expression

    for ancestor in reversed(raw_ancestors):
        left = assignment_left(ancestor)
        if left is not None and contains_descendant(left, raw_identifier):
            if _selectors_containing_identifier(left, raw_identifier):
                return True, False
            if is_read_write_assignment_expression(ancestor):
                return True, True
            return False, True

        operand = unary_write_operand(ancestor)
        if operand is not None and contains_descendant(operand, raw_identifier):
            return True, True

    return True, False


def identifier_access_modes(ctx: "Context", raw_identifier: SyntaxNode) -> tuple[bool, bool]:
    return _identifier_access_modes_over_ancestors([a.raw for a in ctx.stack], raw_identifier)


def enclosing_procedural_block(ctx: "Context") -> "BaseVNode | None":
    from ..syntax_queries import is_procedural_block

    for ancestor in reversed(ctx.stack):
        if is_procedural_block(ancestor.raw):
            return ancestor
    return None


def enclosing_primitive_instantiation(ctx: "Context") -> "BaseVNode | None":
    for ancestor in reversed(ctx.stack):
        if getattr(ancestor.raw, "kind", None) == PRIMITIVE_INSTANTIATION_KIND:
            return ancestor
    return None


def enclosing_continuous_assign(ctx: "Context") -> "BaseVNode | None":
    from ..syntax_queries import is_continuous_assign

    for ancestor in reversed(ctx.stack):
        if is_continuous_assign(ancestor.raw):
            return ancestor
    return None


def enclosing_subroutine_declaration(ctx: "Context") -> "BaseVNode | None":
    from ..syntax_kinds import FUNCTION_DECLARATION_KIND, TASK_DECLARATION_KIND

    for ancestor in reversed(ctx.stack):
        kind = getattr(ancestor.raw, "kind", None)
        if kind in (TASK_DECLARATION_KIND, FUNCTION_DECLARATION_KIND):
            return ancestor
    return None



def enclosing_port_connection(ctx: "Context") -> "BaseVNode | None":
    """Return the nearest ancestor that is an instance port-connection node
    (see `is_port_connection_node`), or `None`. READ_BEFORE_WRITE and
    NO_UNDRIVEN_SIGNAL use this to recognize an identifier wired into an
    instance port and exclude it from their read/write bookkeeping: such an
    identifier is always recorded as a plain read regardless of which side of
    the connection actually drives the net (see `is_port_connection_node`'s
    docstring for why direction can't be resolved here), so treating that read
    as meaningful would misreport a net genuinely driven by the instance's
    output port as never written.
    """
    from ..syntax_queries import is_port_connection_node

    for ancestor in reversed(ctx.stack):
        if is_port_connection_node(ancestor.raw):
            return ancestor
    return None


def enclosing_for_loop_ids(ctx: "Context") -> tuple[str, ...]:
    """Return a location-based id for *every* enclosing `for` loop
    (`ForLoopStatementSyntax`), innermost first, or `()` if none.

    `COMBINATIONAL_LOOP` uses this to recognize a cycle entirely contained
    within one `for` loop's iteration structure -- the standard unrolled
    accumulator idiom (`for (i=0;...) begin acc = acc ^ x[i]; end`, or a
    nested carry-save accumulator where `next_rdt`/`next_rd` are
    updated directly in the outer loop and `next_rdt`'s low bits in an
    inner loop nested inside it) reuses one variable name for both
    "previous" and "new" value across iterations, which a static,
    non-unrolled read/write graph cannot distinguish from genuine
    simultaneous feedback without this hint. Returning every enclosing loop
    (not just the nearest) lets two edges at *different* nesting depths
    still be recognized as part of the same overall unrolled computation
    when they share an outer loop in common, via a shared-id check rather
    than requiring the exact same nearest loop.
    """
    ids: list[str] = []
    for ancestor in reversed(ctx.stack):
        if getattr(ancestor.raw, "kind", None) == FOR_LOOP_STATEMENT_KIND:
            loc = ancestor.location
            ids.append(f"loop:{loc.get('file', '')}:{loc['line']}:{loc['col']}")
    return tuple(ids)


def enclosing_assignment_expression(ctx: "Context") -> "BaseVNode | None":
    """Return the nearest ancestor that is itself an assignment expression
    (`a = b`, `a <= b`, or a compound form like `a += b`) -- the single
    statement whose own left/right-hand sides an identifier occurrence
    belongs to.

    Unlike `enclosing_procedural_block` (one id per *entire* `always` block,
    however many assignment statements it contains), this identifies one
    specific statement -- used by `COMBINATIONAL_LOOP` so a read only links to
    a write when that write's own expression actually reads it, not merely
    because both sit somewhere in the same block (block-level granularity
    fabricates false dependency cycles).
    """
    from ..syntax_queries import is_assignment_expression

    for ancestor in reversed(ctx.stack):
        if is_assignment_expression(ancestor.raw):
            return ancestor
    return None


def is_combinational_driver_block(driver_block: "BaseVNode") -> bool:
    from ..syntax_queries import is_combinational_style_always_block, is_continuous_assign

    raw = driver_block.raw
    return (
        is_continuous_assign(raw)
        or getattr(raw, "kind", None) == ALWAYS_COMB_BLOCK_KIND
        or is_combinational_style_always_block(raw)
    )


def is_sequential_driver_block(driver_block: "BaseVNode") -> bool:
    from .procedural import is_sequential_style_procedural_block

    return is_sequential_style_procedural_block(driver_block.raw)


def is_initial_driver_block(driver_block: "BaseVNode") -> bool:
    from ..syntax_kinds import INITIAL_BLOCK_KIND

    return getattr(driver_block.raw, "kind", None) == INITIAL_BLOCK_KIND



def enclosing_case_statement(ctx: "Context") -> "BaseVNode | None":
    from ..syntax_queries import is_case_statement

    for ancestor in reversed(ctx.stack):
        if is_case_statement(ancestor.raw):
            return ancestor
    return None


def _conditional_references_any_name(raw: object, names: set[str]) -> bool:
    from .procedural import _iter_identifier_nodes

    predicate = getattr(raw, "predicate", None)
    conditions = getattr(predicate, "conditions", None) or []
    for condition in conditions:
        expr = getattr(condition, "expr", None)
        if expr is None:
            continue
        for name, _identifier in _iter_identifier_nodes(expr):
            if name in names:
                return True
    return False


def is_within_async_reset_conditional(ctx: "Context") -> bool:
    """True if the current traversal position is inside a conditional whose
    predicate references one of the enclosing procedural block's async-reset
    sensitivity-list signals -- e.g. inside the `if (rst)`/`else` of
    `always @(posedge clk or posedge rst) if (rst) ...`. Used by
    `ASYNC_RESET_XZ_VALUE`; deliberately does not distinguish the
    reset-asserted branch from the other one (avoids guessing at polarity
    conventions like `if(rst)` vs `if(!rst_n)` vs `if(rst_n==0)`), and
    deliberately does not attempt a sync-reset block at all, since a
    sync-reset signal has no structural marker to find it by.
    """
    from ..syntax_queries import async_reset_signal_names, is_conditional_statement

    block = enclosing_procedural_block(ctx)
    if block is None:
        return False
    reset_names = async_reset_signal_names(block.raw)
    if not reset_names:
        return False

    for ancestor in reversed(ctx.stack):
        if ancestor is block:
            break
        if is_conditional_statement(ancestor.raw) and _conditional_references_any_name(ancestor.raw, reset_names):
            return True
    return False


@guarded_traversal(max_depth=64, default=False)
def _statement_assigns_register(raw: object, register_name: str) -> bool:
    from ..syntax_queries import assignment_target_identifier_name, is_assignment_expression

    if (
        is_assignment_expression(raw)
        and getattr(raw, "kind", None) == NONBLOCKING_ASSIGNMENT_KIND
        and assignment_target_identifier_name(raw) == register_name
    ):
        return True

    for child in raw_node_children(raw):
        if isinstance(child, SyntaxNode) and not isinstance(child, ProceduralBlockNode):
            if _statement_assigns_register(child, register_name):
                return True
    return False


def is_state_register_reset_covered(block_raw: object, register_name: str) -> bool:
    """True if `block_raw` (a procedural block) contains a conditional whose
    predicate references one of the block's async-reset sensitivity-list
    signals, and whose **`if`-branch specifically** (`.statement`, not
    `.elseClause`) contains a nonblocking assignment to `register_name` --
    i.e. the state register is actually driven to a value in the
    reset-asserted branch, not left entirely to whatever a case statement
    elsewhere would assign. Used by `MISSING_STATE_REGISTER_RESET`.

    Unlike `is_within_async_reset_conditional` (which deliberately doesn't
    distinguish the reset-asserted branch from the other one, since that
    function only needs "is this node near a reset check at all"), this one
    specifically needs to know it's the reset-asserted side -- checking both
    branches indiscriminately would treat `if (rst) other_sig <= 0; else
    case (state) ...` as "covered" for `state` too, since `state` does sit
    inside *a* branch of a conditional that references `rst`; that would make
    the rule almost never fire, since `if (reset) ... else case (state) ...`
    is the standard FSM idiom. Assumes the conventional polarity where reset
    is asserted in the `if`-branch (`if (rst) ...` / `if (!rst_n) ...`, both
    common) -- an inverted style with reset asserted in the `else`-branch
    instead is a known, undetected limitation, same "no polarity guessing"
    restraint already documented elsewhere in this project.

    Returns `False` immediately when the block has no async-reset signals at
    all (`async_reset_signal_names` is empty) -- a sync-reset signal has no
    structural marker to find it by, so a sync-classified block is never
    checked here at all (the rule itself gates on `classify_reset_style(...)
    == "async"` before ever calling this).
    """
    from ..syntax_queries import async_reset_signal_names, is_conditional_statement

    reset_names = async_reset_signal_names(block_raw)
    if not reset_names:
        return False

    @guarded_traversal(max_depth=64, default=False)
    def _walk(node: object) -> bool:
        if is_conditional_statement(node) and _conditional_references_any_name(node, reset_names):
            if _statement_assigns_register(getattr(node, "statement", None), register_name):
                return True

        for child in raw_node_children(node):
            if isinstance(child, SyntaxNode) and not isinstance(child, ProceduralBlockNode):
                if _walk(child):
                    return True
        return False

    return _walk(block_raw)


def identifier_is_assignment_lhs(ctx: "Context", raw_identifier: SyntaxNode) -> bool:
    _read, write = identifier_access_modes(ctx, raw_identifier)
    return write


def assignment_target_identifier_name(raw: object) -> str | None:
    from ..syntax_queries import identifier_name

    left = assignment_left(raw)
    if left is None:
        return None
    return identifier_name(left)


def assignment_right(raw: object) -> SyntaxNode | None:
    from ..syntax_queries import is_assignment_expression

    if not is_assignment_expression(raw):
        return None
    right = getattr(raw, "right", None)
    return right if isinstance(right, SyntaxNode) else None


# Re-exported from .expressions for backward compatibility
__all_expressions = [simple_expression_width_and_signed]

