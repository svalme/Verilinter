"""Assignment target/RHS resolution: extracting and resolving the LHS and RHS
of continuous assignments, procedural assignments, and declarator
initializers, plus element-select (bit/part-select) decoding."""

from ..syntax_kinds import (
    ASCENDING_RANGE_SELECT_KIND,
    BIT_SELECT_KIND,
    DESCENDING_RANGE_SELECT_KIND,
    RANGE_SELECT_KINDS,
    SIMPLE_RANGE_SELECT_KIND,
)
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


def extract_assignment_target_and_selectors(
    raw: object,
    _depth: int = 0,
    _visited: set[int] | None = None,
) -> tuple[str | None, list[SyntaxNode]]:
    """Extract `(base_name, selectors)` from an assignment target node.
    Handles `IdentifierName`, `IdentifierSelectName`, and `ElementSelectExpression`.
    """
    if raw is None or _depth >= 64:
        return None, []
    if _visited is None:
        _visited = set()
    rid = id(raw)
    if rid in _visited:
        return None, []
    _visited.add(rid)

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
        base_name, base_selectors = extract_assignment_target_and_selectors(curr, _depth + 1, _visited)
        return base_name, base_selectors + list(reversed(nested_selectors))
    name = identifier_name(raw)
    return (name if isinstance(name, str) and name else None), []


def resolve_assignment_target(
    target_node: object,
    scope: object,
    tree: object = None,
    _depth: int = 0,
    _visited: set[int] | None = None,
) -> object:
    """Recursively resolve an assignment target expression (single identifier,
    indexed/sliced target, or concatenated target) into an `AssignmentTarget`.
    Returns `None` if the target cannot be resolved or any component has an
    unresolved width.
    """
    if _depth >= 32:
        return None
    raw = getattr(target_node, "raw", target_node)
    if raw is None or scope is None:
        return None
    if _visited is None:
        _visited = set()
    rid = id(raw)
    if rid in _visited:
        return None
    _visited.add(rid)

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
            elem_target = resolve_assignment_target(m, scope, tree, _depth + 1, _visited)
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
        inner_target = resolve_assignment_target(concat_node, scope, tree, _depth + 1, _visited)
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
    scope = getattr(ctx, "scope", lambda: None)()
    tree = getattr(vnode, "tree", None) or getattr(ctx, "tree", None)

    if is_assignment_expression(raw):
        left = assignment_left(raw)
        right = assignment_right(raw)
        if left is None or right is None or scope is None:
            return None, None
        target = resolve_assignment_target(left, scope, tree)
        if target is None:
            return None, None
        return target, right

    if declarator_has_initializer(raw):
        if declarator_is_parameter(ctx):
            return None, None
        name = declarator_name(raw)
        if name is None or scope is None:
            return None, None
        lookup_hierarchical = getattr(scope, "lookup_hierarchical", None)
        symbol = lookup_hierarchical(name) if callable(lookup_hierarchical) else getattr(scope, "lookup", lambda _n: None)(name)
        if symbol is None:
            return None, None
        right = declarator_initializer_expression(raw)
        target = AssignmentTarget(
            base_symbol=symbol,
            slice_width=None,
            is_sliced=False,
        )
        return target, right

    return None, None
