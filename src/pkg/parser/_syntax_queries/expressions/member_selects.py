"""The width of a member select of a struct variable (`bus.addr`, `inputs[0].valid`)."""
from __future__ import annotations

from ...syntax_kinds import DOT_TOKEN_KIND, IDENTIFIER_NAME_KIND, IDENTIFIER_SELECT_NAME_KIND, SCOPED_NAME_KIND
from ..shared import identifier_name
from .symbol_resolution import resolve_symbol_in_scope


def member_select_width_and_signed(scope: object, expr: object) -> tuple[int | None, bool | None]:
    """`(width, None)` of `variable.member` or `array[i].member` when the variable's type is a packed struct or
    union whose member widths are known; `(None, None)` for any other name path."""
    if getattr(expr, "kind", None) != SCOPED_NAME_KIND:
        return None, None
    if getattr(getattr(expr, "separator", None), "kind", None) != DOT_TOKEN_KIND:
        return None, None
    left, right = getattr(expr, "left", None), getattr(expr, "right", None)
    if getattr(left, "kind", None) not in (IDENTIFIER_NAME_KIND, IDENTIFIER_SELECT_NAME_KIND):
        return None, None
    if getattr(right, "kind", None) != IDENTIFIER_NAME_KIND:
        return None, None
    base_name, member_name = identifier_name(left), identifier_name(right)
    if not base_name or not member_name or scope is None:
        return None, None
    members = getattr(resolve_symbol_in_scope(scope, base_name), "member_widths", None)
    width = members.get(member_name) if isinstance(members, dict) else None
    return (width, None) if isinstance(width, int) else (None, None)
