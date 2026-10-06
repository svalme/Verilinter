"""Assignment target/RHS resolution: extracting and resolving the LHS and RHS
of continuous assignments, procedural assignments, and declarator
initializers, plus element-select (bit/part-select) decoding."""

from ..syntax_kinds import (
    ASCENDING_RANGE_SELECT_KIND,
    BIT_SELECT_KIND,
    DESCENDING_RANGE_SELECT_KIND,
    RANGE_SELECT_KINDS,
    READ_WRITE_ASSIGNMENT_KINDS,
    SIMPLE_RANGE_SELECT_KIND,
    UNARY_MINUS_EXPRESSION_KIND,
    UNARY_PLUS_EXPRESSION_KIND,
)
from ..traversal_guard import guarded_traversal
from ..types import IdentifierSelectNameNode, SyntaxNode
from .declarators import (
    declarator_has_initializer,
    declarator_initializer_expression,
    declarator_is_parameter,
    declarator_name,
)
from .shared import identifier_name


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
        if inner_kind == SIMPLE_RANGE_SELECT_KIND:
            shape = "simple_range"
        elif inner_kind == ASCENDING_RANGE_SELECT_KIND:
            shape = "ascending"
        elif inner_kind == DESCENDING_RANGE_SELECT_KIND:
            shape = "descending"
        else:
            shape = None
        return (shape, (left, right)) if shape is not None else None
    return None


def is_ascending_range_select(raw: object) -> bool:
    return getattr(raw, "kind", None) == ASCENDING_RANGE_SELECT_KIND


def is_descending_range_select(raw: object) -> bool:
    return getattr(raw, "kind", None) == DESCENDING_RANGE_SELECT_KIND


def is_indexed_part_select(raw: object) -> bool:
    return getattr(raw, "kind", None) in (ASCENDING_RANGE_SELECT_KIND, DESCENDING_RANGE_SELECT_KIND)


def indexed_part_select_width_expression(raw: object) -> SyntaxNode | None:
    if not is_indexed_part_select(raw):
        return None
    width_node = getattr(raw, "right", None)
    return width_node if isinstance(width_node, SyntaxNode) else None


def is_reversed_indexed_part_select(raw: object) -> bool:
    """True if `raw` is a SimpleRangeSelect syntax node where `: +` or `: -`
    was typed with `: ` immediately followed by `+` or `-` without intervening whitespace
    (e.g. `r[2 :+ 1]` or `r[2 :- 1]`), which is almost certainly a typo for
    `+:` or `-:`."""
    if getattr(raw, "kind", None) != SIMPLE_RANGE_SELECT_KIND:
        return False
    right = getattr(raw, "right", None)
    if right is None:
        return False
    rk = getattr(right, "kind", None)
    if rk not in (UNARY_PLUS_EXPRESSION_KIND, UNARY_MINUS_EXPRESSION_KIND):
        return False
    colon_tok = getattr(raw, "range", None)
    op_tok = getattr(right, "operatorToken", None)
    if colon_tok is None or op_tok is None:
        return False
    colon_range = getattr(colon_tok, "range", None)
    op_range = getattr(op_tok, "range", None)
    if colon_range is None or op_range is None:
        return False
    return getattr(colon_range, "end", None) == getattr(op_range, "start", None)


def is_illegal_indexed_part_select_width(raw: object, scope: object = None) -> bool:
    """True if `raw` is an indexed part-select (`+:` or `-:`) whose width
    expression violates IEEE 1800-2017 §11.5.1:
    - Width expression must evaluate to a positive constant integer expression (> 0).
    - Width expression cannot be non-constant (variable, wire, reg, logic, etc.)."""
    if not is_indexed_part_select(raw):
        return False
    width_node = getattr(raw, "right", None)
    if width_node is None:
        return True

    from .expressions import evaluate_constant_expression
    from .procedural import _iter_identifier_nodes

    val = evaluate_constant_expression(width_node, scope=scope)
    if val is not None:
        return val <= 0

    idents = list(_iter_identifier_nodes(width_node))
    if not idents:
        return True

    if scope is not None:
        for name, _ident_node in idents:
            if not name:
                continue
            sym = scope.lookup_hierarchical(name)
            if sym is not None:
                is_const = (
                    getattr(sym, "is_constant", False)
                    or getattr(sym, "is_localparam", False)
                    or getattr(sym, "kind", "") == "parameter"
                )
                if not is_const:
                    return True
            else:
                return True
    else:
        return True
    return False


@guarded_traversal(max_depth=64, default=(None, []))
def extract_assignment_target_and_selectors(
    raw: object,
) -> tuple[str | None, list[SyntaxNode]]:
    """Extract `(base_name, selectors)` from an assignment target node.
    Handles `IdentifierName`, `IdentifierSelectName`, and `ElementSelectExpression`.
    """
    if raw is None:
        return None, []

    from ..syntax_kinds import (
        ELEMENT_SELECT_EXPRESSION_KIND,
        IDENTIFIER_NAME_KIND,
        IDENTIFIER_SELECT_NAME_KIND,
    )

    kind = getattr(raw, "kind", None)
    if kind == IDENTIFIER_NAME_KIND:
        ident = getattr(raw, "identifier", None)
        name = getattr(ident, "value", None)
        return (name if isinstance(name, str) and name else None), []
    if kind == IDENTIFIER_SELECT_NAME_KIND:
        ident = getattr(raw, "identifier", None)
        name = getattr(ident, "value", None)
        selectors = getattr(raw, "selectors", None)
        sels = [s for s in selectors if isinstance(s, SyntaxNode)] if selectors else []
        return (name if isinstance(name, str) and name else None), sels
    if kind == ELEMENT_SELECT_EXPRESSION_KIND:
        nested_selectors: list[SyntaxNode] = []
        curr = raw
        depth = 0
        seen_curr: set[int] = set()
        while getattr(curr, "kind", None) == ELEMENT_SELECT_EXPRESSION_KIND and depth < 64:
            cid = id(curr)
            if cid in seen_curr:
                break
            seen_curr.add(cid)
            depth += 1
            sel = getattr(curr, "select", None)
            if isinstance(sel, SyntaxNode):
                nested_selectors.append(sel)
            curr = getattr(curr, "left", None)
        base_name, base_selectors = extract_assignment_target_and_selectors(curr)
        return base_name, base_selectors + list(reversed(nested_selectors))
    name = identifier_name(raw)
    return (name if isinstance(name, str) and name else None), []


@guarded_traversal(max_depth=32, default=None)
def resolve_assignment_target(
    target_node: object,
    scope: object,
    tree: object = None,
) -> object:
    """Recursively resolve an assignment target expression (single identifier,
    indexed/sliced target, or concatenated target) into an `AssignmentTarget`.
    Returns `None` if the target cannot be resolved or any component has an
    unresolved width.
    """
    raw = getattr(target_node, "raw", target_node)
    if raw is None or scope is None:
        return None

    from ...semantic.models.assignment_target import AssignmentTarget
    from ..syntax_kinds import (
        CONCATENATION_EXPRESSION_KIND,
        MULTIPLE_CONCATENATION_EXPRESSION_KIND,
    )
    from ..syntax_queries import (
        compute_sliced_width,
        evaluate_constant_expression,
        unwrap_parentheses,
    )

    raw = unwrap_parentheses(raw)
    kind = getattr(raw, "kind", None)

    if kind == CONCATENATION_EXPRESSION_KIND:
        raw_exprs = getattr(raw, "expressions", None)
        if raw_exprs is None:
            return None
        members = [e for e in raw_exprs if isinstance(e, SyntaxNode)]
        if not members:
            return None
        elements: list[AssignmentTarget] = []
        total_w = 0
        for m in members:
            elem_target = resolve_assignment_target(m, scope, tree)
            if elem_target is None or not isinstance(getattr(elem_target, "bit_width", None), int):
                return None
            elements.append(elem_target)
            total_w += elem_target.bit_width
        return AssignmentTarget(
            is_concatenated=True,
            elements=elements,
            total_width=total_w,
        )

    if kind == MULTIPLE_CONCATENATION_EXPRESSION_KIND:
        count_node = unwrap_parentheses(getattr(raw, "expression", None))
        concat_node = unwrap_parentheses(getattr(raw, "concatenation", None))
        count = evaluate_constant_expression(count_node, scope=scope)
        if count is None or not isinstance(count, int) or count <= 0 or concat_node is None:
            return None
        inner_target = resolve_assignment_target(concat_node, scope, tree)
        if inner_target is None or not isinstance(getattr(inner_target, "bit_width", None), int):
            return None
        return AssignmentTarget(
            is_concatenated=True,
            elements=[inner_target] * count,
            total_width=count * inner_target.bit_width,
        )

    name, selectors = extract_assignment_target_and_selectors(raw)
    if name is None:
        return None
    lookup_hierarchical = getattr(scope, "lookup_hierarchical", None)
    symbol = lookup_hierarchical(name) if callable(lookup_hierarchical) else getattr(scope, "lookup", lambda _n: None)(name)
    if symbol is None:
        return None
    if selectors:
        slice_w = compute_sliced_width(symbol, selectors, scope=scope)
        return AssignmentTarget(
            base_symbol=symbol,
            slice_width=slice_w,
            is_sliced=True,
            selectors=selectors,
        )
    return AssignmentTarget(
        base_symbol=symbol,
        slice_width=None,
        is_sliced=False,
    )


def resolve_assignment_target_and_rhs(vnode: object, ctx: object):
    """Unpack an assignment-like construct -- continuous assignment, procedural
    assignment, or variable declarator initializer -- returning
    `(lhs_target, right_expr)` resolved against `ctx.scope()`.
    Returns `(None, None)` when the construct is not an assignment or the
    target cannot be resolved.
    """
    from ...semantic.models.assignment_target import AssignmentTarget
    from ..syntax_queries import (
        assignment_left,
        assignment_right,
        is_assignment_expression,
    )

    raw = getattr(vnode, "raw", vnode)
    # Compound operations are not plain value transfers. Comparing their
    # RHS alone with the destination width/sign would produce false alarms.
    if getattr(raw, "kind", None) in READ_WRITE_ASSIGNMENT_KINDS:
        return None, None

    ctx_data = getattr(ctx, "data", None)
    module_cache = ctx_data.get("module_cache") if isinstance(ctx_data, dict) else None
    cache_key = ("assign_target_rhs", id(raw))
    if isinstance(module_cache, dict) and cache_key in module_cache:
        return module_cache[cache_key]

    def _store(res: tuple[object, object]) -> tuple[object, object]:
        if isinstance(module_cache, dict):
            module_cache[cache_key] = res
        return res

    scope = getattr(ctx, "scope", lambda: None)()
    tree = getattr(vnode, "tree", None) or getattr(ctx, "tree", None)

    if is_assignment_expression(raw):
        left = assignment_left(raw)
        right = assignment_right(raw)
        if left is None or right is None or scope is None:
            return _store((None, None))
        target = resolve_assignment_target(left, scope, tree)
        if target is None:
            return _store((None, None))
        return _store((target, right))

    if declarator_has_initializer(raw):
        if declarator_is_parameter(ctx):
            return _store((None, None))
        name = declarator_name(raw)
        if name is None or scope is None:
            return _store((None, None))
        lookup_hierarchical = getattr(scope, "lookup_hierarchical", None)
        symbol = lookup_hierarchical(name) if callable(lookup_hierarchical) else getattr(scope, "lookup", lambda _n: None)(name)
        if symbol is None:
            return _store((None, None))
        right = declarator_initializer_expression(raw)
        target = AssignmentTarget(
            base_symbol=symbol,
            slice_width=None,
            is_sliced=False,
        )
        return _store((target, right))

    return _store((None, None))
