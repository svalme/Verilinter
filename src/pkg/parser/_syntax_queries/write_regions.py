from ..syntax_kinds import DOT_TOKEN_KIND, SCOPED_NAME_KIND
from ...semantic.write_region import FIELD, INDEX, RANGE
from ..traversal_guard import guarded_traversal
from .expressions import evaluate_constant_expression
from .shapes import element_select_index_or_range
from .shared import identifier_name

_MAX_MEMBER_DEPTH = 32


def _selector_steps(selectors: object, scope: object) -> list[tuple[object, ...]]:
    """One region step per `[...]` selector, in order. A selector that cannot be read still takes its
    position, so later steps stay aligned with the same dimension in another write."""
    steps: list[tuple[object, ...]] = []
    for selector in selectors or ():
        unwrapped = element_select_index_or_range(selector)
        if unwrapped is None:
            steps.append((RANGE, None, None))
            continue
        shape, payload = unwrapped
        if shape == "bit":
            steps.append((INDEX, evaluate_constant_expression(payload, scope=scope)))
            continue
        left, right = payload  # type: ignore[misc]
        first = evaluate_constant_expression(left, scope=scope)
        second = evaluate_constant_expression(right, scope=scope)
        if first is None or second is None:
            steps.append((RANGE, None, None))
        elif shape == "simple_range":
            steps.append((RANGE, min(first, second), max(first, second)))
        elif second <= 0:
            steps.append((RANGE, None, None))
        elif shape == "ascending":
            steps.append((RANGE, first, first + second - 1))
        else:
            steps.append((RANGE, first - second + 1, first))
    return steps


@guarded_traversal(max_depth=64, default=())
def write_region_of_identifier(raw_identifier: object, scope: object) -> tuple[tuple[object, ...], ...]:
    """The part of its symbol that a write through `raw_identifier` touches (see `semantic.write_region`).

    Takes the selectors on the name itself, then each `.member` and the member's own selectors while the
    name is the left side of a dotted name. Anything it does not recognise ends the walk, which leaves a
    shorter region and so a larger part of the symbol."""
    steps = _selector_steps(getattr(raw_identifier, "selectors", None), scope)
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
        steps.extend(_selector_steps(getattr(member, "selectors", None), scope))
        node = parent
    return tuple(steps)
