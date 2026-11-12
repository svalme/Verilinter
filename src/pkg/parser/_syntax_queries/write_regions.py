from ..syntax_kinds import DOT_TOKEN_KIND, SCOPED_NAME_KIND
from ...semantic.write_region import FIELD, INDEX, NEVER, RANGE, span_step
from ..traversal_guard import guarded_traversal
from .expressions import evaluate_constant_expression
from .generate_loops import evaluate_under, generate_bindings
from .shapes import element_select_index_or_range
from .shared import identifier_name

_MAX_MEMBER_DEPTH = 32


def _selector_values(selector: object, scope: object, binding: dict[str, int]) -> tuple[str, int | None, int | None] | None:
    """`("index", v, v)` or `("range", low, high)` for one `[...]` selector under `binding`; the numbers are
    None when they cannot be evaluated. None when the selector is not a recognised shape."""
    unwrapped = element_select_index_or_range(selector)
    if unwrapped is None:
        return None
    shape, payload = unwrapped
    if shape == "bit":
        value = evaluate_under(payload, scope, binding)
        return (INDEX, value, value)
    left, right = payload  # type: ignore[misc]
    first = evaluate_under(left, scope, binding)
    second = evaluate_under(right, scope, binding)
    if first is None or second is None:
        return (RANGE, None, None)
    if shape == "simple_range":
        return (RANGE, min(first, second), max(first, second))
    if second <= 0:
        return (RANGE, None, None)
    if shape == "ascending":
        return (RANGE, first, first + second - 1)
    return (RANGE, first - second + 1, first)


def _selector_steps(
    selectors: object, scope: object, bindings: list[dict[str, int]] | None
) -> list[tuple[object, ...]]:
    """One region step per `[...]` selector, in order. A selector that cannot be read still takes its
    position, so later steps stay aligned with the same dimension in another write. Under several
    generate-loop bindings a step covers every value its selector takes."""
    steps: list[tuple[object, ...]] = []
    for selector in selectors or ():
        values = [_selector_values(selector, scope, binding) for binding in (bindings or [{}])]
        if any(v is None or v[1] is None or v[2] is None for v in values):
            kinds = {v[0] for v in values if v is not None}
            steps.append((INDEX, None) if kinds == {INDEX} else (RANGE, None, None))
            continue
        steps.append(span_step((v[1], v[2]) for v in values))  # type: ignore[union-attr,misc]
    return steps


@guarded_traversal(max_depth=64, default=())
def write_region_of_identifier(raw_identifier: object, scope: object) -> tuple[tuple[object, ...], ...]:
    """The part of its symbol that a write through `raw_identifier` touches (see `semantic.write_region`).

    Takes the selectors on the name itself, then each `.member` and the member's own selectors while the
    name is the left side of a dotted name. Anything it does not recognise ends the walk, which leaves a
    shorter region and so a larger part of the symbol."""
    bindings = generate_bindings(raw_identifier, scope)
    if bindings is not None and not bindings:
        return ((NEVER,),)
    steps = _selector_steps(getattr(raw_identifier, "selectors", None), scope, bindings)
    node = raw_identifier
    for _ in range(_MAX_MEMBER_DEPTH):
        parent = getattr(node, "parent", None)
        if (
            getattr(parent, "kind", None) != SCOPED_NAME_KIND
            or getattr(getattr(parent, "separator", None), "kind", None) != DOT_TOKEN_KIND
            or getattr(parent, "left", None) is not node
        ):
            break
        member = getattr(parent, "right", None)
        member_name = identifier_name(member)
        if member_name is None:
            break
        steps.append((FIELD, member_name))
        steps.extend(_selector_steps(getattr(member, "selectors", None), scope, bindings))
        node = parent
    return tuple(steps)
