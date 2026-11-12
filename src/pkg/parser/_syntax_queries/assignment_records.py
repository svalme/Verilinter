from ..syntax_kinds import CONCATENATION_EXPRESSION_KIND, DOT_TOKEN_KIND, NONBLOCKING_ASSIGNMENT_KIND, SCOPED_NAME_KIND
from ..traversal_guard import guarded_traversal
from ..types import SyntaxNode
from .access import assignment_left, assignment_right, enclosing_continuous_assign, enclosing_procedural_block
from .declarators import declarator_has_initializer, declarator_initializer_expression, declarator_is_parameter, declarator_name
from .literals import is_assignment_expression, is_read_write_assignment_expression
from .node_cache import MISSING, extract_module_cache, node_cache_get, node_cache_put
from .shapes import extract_assignment_target_and_selectors
from .write_regions import write_region_of_identifier

_RECORD_CACHE_TAG = "assignment_record"
_MAX_TARGET_DEPTH = 64


def driver_id_of(driver_block: object) -> str:
    """The id a use event records for the procedural block or continuous assign that owns a write."""
    location = driver_block.location  # type: ignore[attr-defined]
    return f"{driver_block.kind}:{location.get('file', '')}:{location['line']}:{location['col']}"  # type: ignore[attr-defined]


def _statement_id(location: dict) -> str:
    return f"stmt:{location.get('file', '')}:{location['line']}:{location['col']}"


def _base_reference(raw: object) -> object:
    """The leftmost name of a dotted reference: `t[1]` for `t[1].b[2]`, the node itself otherwise."""
    for _ in range(_MAX_TARGET_DEPTH):
        if getattr(raw, "kind", None) == SCOPED_NAME_KIND and getattr(getattr(raw, "separator", None), "kind", None) == DOT_TOKEN_KIND:
            raw = getattr(raw, "left", None)
            continue
        break
    return raw


def assignment_kind_of(raw: object, continuous: bool = False):
    """The `AssignmentKind` of an assignment expression node, or None for any other node. A compound
    form (`x += y`) is its own kind; `continuous` says the assignment sits in a continuous assign."""
    from ...semantic.models.assignment_record import AssignmentKind

    if not is_assignment_expression(raw):
        return None
    if is_read_write_assignment_expression(raw):
        return AssignmentKind.COMPOUND
    if getattr(raw, "kind", None) == NONBLOCKING_ASSIGNMENT_KIND:
        return AssignmentKind.NONBLOCKING
    return AssignmentKind.CONTINUOUS if continuous else AssignmentKind.BLOCKING


@guarded_traversal(max_depth=64, default=())
def target_leaves(left: object) -> tuple:
    """The written references of a left-hand side as syntax nodes, in source order: the node itself,
    or each member of a concatenation. Parentheses are removed."""
    from ..syntax_queries import unwrap_parentheses

    left = unwrap_parentheses(left)
    if getattr(left, "kind", None) == CONCATENATION_EXPRESSION_KIND:
        found: list = []
        for member in getattr(left, "expressions", None) or ():
            if isinstance(member, SyntaxNode):
                found.extend(target_leaves(member))
        return tuple(found)
    return (left,)


def _lookup(scope: object, name: str) -> object | None:
    lookup_hierarchical = getattr(scope, "lookup_hierarchical", None)
    return lookup_hierarchical(name) if callable(lookup_hierarchical) else getattr(scope, "lookup", lambda _n: None)(name)


def _leaf_target(raw: object, scope: object):
    from ...semantic.models.assignment_target import AssignmentTarget
    from ..syntax_queries import compute_sliced_width

    base = _base_reference(raw)
    name, selectors = extract_assignment_target_and_selectors(base)
    symbol = _lookup(scope, name) if name is not None and scope is not None else None
    through_member = base is not raw
    is_sliced = bool(selectors) or through_member
    slice_width = None
    if symbol is not None and selectors and not through_member:
        slice_width = compute_sliced_width(symbol, selectors, scope=scope)
    return AssignmentTarget(
        base_symbol=symbol,
        slice_width=slice_width,
        is_sliced=is_sliced,
        selectors=selectors,
        reference=raw,
        write_region=write_region_of_identifier(base, scope) if symbol is not None else (),
    )


def _targets_of(raw: object, scope: object) -> tuple:
    """One `AssignmentTarget` per written reference of a left-hand side, in source order."""
    return tuple(_leaf_target(leaf, scope) for leaf in target_leaves(raw))


def _build_record(ctx: object, vnode: object):
    from ...semantic.models.assignment_record import AssignmentKind, AssignmentRecord

    raw = getattr(vnode, "raw", None)
    location = getattr(vnode, "location", None)
    scope = getattr(ctx, "scope", lambda: None)()
    if raw is None or location is None or scope is None:
        return None

    if is_assignment_expression(raw):
        left, right = assignment_left(raw), assignment_right(raw)
        if left is None or right is None:
            return None
        kind = assignment_kind_of(raw, continuous=enclosing_continuous_assign(ctx) is not None)
        targets = _targets_of(left, scope)
    elif declarator_has_initializer(raw) and not declarator_is_parameter(ctx):
        name = declarator_name(raw)
        right = declarator_initializer_expression(raw)
        if name is None or right is None:
            return None
        symbol = _lookup(scope, name)
        from ...semantic.models.assignment_target import AssignmentTarget

        kind = AssignmentKind.INITIALIZER
        targets = (AssignmentTarget(base_symbol=symbol),)
    else:
        return None

    driver = enclosing_procedural_block(ctx) or enclosing_continuous_assign(ctx)
    return AssignmentRecord(
        node=raw,
        kind=kind,
        targets=targets,
        rhs=right,
        driver_id=driver_id_of(driver) if driver is not None else None,
        driver_location=driver.location if driver is not None else None,
        statement_id=_statement_id(location),
        location=location,
    )


def assignment_record(ctx: object, vnode: object):
    """The `AssignmentRecord` for an assignment expression, a continuous assign's assignment or a
    declarator with an initializer; None for any other node. Built once per node and kept in the
    module cache, so every rule that asks gets the same answer."""
    raw = getattr(vnode, "raw", None)
    cache = extract_module_cache(ctx)
    cached = node_cache_get(cache, _RECORD_CACHE_TAG, raw)
    if cached is not MISSING:
        return cached
    record = _build_record(ctx, vnode)
    node_cache_put(cache, _RECORD_CACHE_TAG, raw, record)
    return record
