"""The packed width of a data type written in a declaration, and of the members of a packed struct or union.

Covers vector types (`logic [7:0]`), integer atoms (`int`, `byte`), enums, packed structs and unions, and a
named type that resolves to a typedef whose width is known.
"""
from __future__ import annotations

from ...syntax_kinds import ENUM_TYPE_KIND, IDENTIFIER_SELECT_NAME_KIND, NAMED_TYPE_KIND, SCOPED_NAME_KIND
from ...traversal_guard import guarded_traversal
from ...types import SyntaxNode
from ..shared import identifier_name
from .constant_evaluation import evaluate_constant_expression
from .symbol_resolution import resolve_package_member_in_scope, resolve_symbol_in_scope

_ATOM_WIDTHS = {"int": 32, "integer": 32, "shortint": 16, "longint": 64, "byte": 8, "time": 64}
_UNSIGNED_BY_DEFAULT = {"time"}
_VECTOR_KEYWORDS = {"logic", "bit", "reg"}


def _keyword(data_type: object) -> str | None:
    return getattr(getattr(data_type, "keyword", None), "valueText", None)


def _signing(data_type: object) -> str | None:
    return getattr(getattr(data_type, "signing", None), "valueText", None) or None


def dimensions_width(dimensions: object, scope: object) -> int | None:
    """The number of bits the packed dimensions `[a:b][c:d]` give together, or None when one is unknown."""
    total = 1
    for dimension in dimensions or ():
        if not isinstance(dimension, SyntaxNode):
            continue
        selector = getattr(getattr(dimension, "specifier", None), "selector", None)
        left, right = getattr(selector, "left", None), getattr(selector, "right", None)
        if left is None or right is None:
            return None
        msb = evaluate_constant_expression(left, scope=scope)
        lsb = evaluate_constant_expression(right, scope=scope)
        if msb is None or lsb is None:
            return None
        total *= abs(msb - lsb) + 1
    return total


def named_type_dimensions_width(name: object, scope: object) -> int | None:
    """The bits that the packed dimensions written after a type name give (`s_t [1:0] x`, where the name
    node is `s_t[1:0]`); 1 when there are none, None when one is unknown."""
    if getattr(name, "kind", None) != IDENTIFIER_SELECT_NAME_KIND:
        return 1
    total = 1
    for select in getattr(name, "selectors", ()) or ():
        if not isinstance(select, SyntaxNode):
            continue
        selector = getattr(select, "selector", None)
        left, right = getattr(selector, "left", None), getattr(selector, "right", None)
        if left is None or right is None:
            return None
        msb = evaluate_constant_expression(left, scope=scope)
        lsb = evaluate_constant_expression(right, scope=scope)
        if msb is None or lsb is None:
            return None
        total *= abs(msb - lsb) + 1
    return total


def _named_type_symbol(data_type: object, scope: object) -> object | None:
    name = getattr(data_type, "name", None)
    if getattr(name, "kind", None) == SCOPED_NAME_KIND:
        package = identifier_name(getattr(name, "left", None))
        member = identifier_name(getattr(name, "right", None))
        symbol = resolve_package_member_in_scope(scope, package, member) if package and member else None
    else:
        type_name = identifier_name(name)
        symbol = resolve_symbol_in_scope(scope, type_name) if type_name else None
    return symbol


def packed_member_widths(data_type: object, scope: object) -> dict[str, int] | None:
    """`{member name: width}` of a packed struct or union, or None for any other type or when a member's
    width is unknown."""
    members = getattr(data_type, "members", None)
    is_packed = getattr(getattr(data_type, "packed", None), "valueText", "") == "packed"
    if members is None or not is_packed or getattr(data_type, "baseType", None) is not None:
        return None
    widths: dict[str, int] = {}
    for member in members:
        if not isinstance(member, SyntaxNode):
            continue
        member_width, _signed = packed_type_width_and_signed(getattr(member, "type", None), scope)
        if member_width is None:
            return None
        for declarator in getattr(member, "declarators", ()) or ():
            if not isinstance(declarator, SyntaxNode):
                continue
            if any(isinstance(d, SyntaxNode) for d in getattr(declarator, "dimensions", ()) or ()):
                return None
            name = identifier_name(getattr(declarator, "name", None))
            if name:
                widths[name] = member_width
    return widths


@guarded_traversal(node_arg="data_type", max_depth=32, default=(None, None))
def packed_type_width_and_signed(data_type: object, scope: object) -> tuple[int | None, bool | None]:
    """`(width, signed)` of a data type, with None for each part that is not known."""
    if data_type is None:
        return None, None
    kind = getattr(data_type, "kind", None)
    keyword = _keyword(data_type)
    signing = _signing(data_type)
    dimensions = getattr(data_type, "dimensions", None)

    if kind == NAMED_TYPE_KIND:
        symbol = _named_type_symbol(data_type, scope)
        width = getattr(symbol, "bit_width", None)
        if not isinstance(width, int):
            return None, None
        extra = named_type_dimensions_width(getattr(data_type, "name", None), scope)
        return (width * extra if extra is not None else None), getattr(symbol, "is_signed", None)

    members = getattr(data_type, "members", None)
    if members is not None and kind != ENUM_TYPE_KIND:
        widths = packed_member_widths(data_type, scope)
        if widths is None:
            return None, None
        widths_by_member = [widths[name] for name in widths]
        total = sum(widths_by_member) if keyword == "struct" else max(widths_by_member, default=0)
        extra = dimensions_width(dimensions, scope)
        return (total * extra if extra is not None else None), signing == "signed"

    if kind == ENUM_TYPE_KIND:
        base = getattr(data_type, "baseType", None)
        if base is None:
            return 32, True
        return packed_type_width_and_signed(base, scope)

    if keyword in _ATOM_WIDTHS:
        signed = signing != "unsigned" and keyword not in _UNSIGNED_BY_DEFAULT
        return _ATOM_WIDTHS[keyword], signed

    if keyword in _VECTOR_KEYWORDS:
        width = dimensions_width(dimensions, scope)
        return width, signing == "signed"

    return None, None


def typedef_layout(raw: object, scope: object) -> tuple[int | None, bool | None, dict[str, int] | None]:
    """`(width, signed, member widths)` of what a `typedef` declaration names. A typedef with unpacked
    dimensions after its name is an array type and has no packed width."""
    if any(isinstance(d, SyntaxNode) for d in getattr(raw, "dimensions", ()) or ()):
        return None, None, None
    data_type = getattr(raw, "type", None)
    width, signed = packed_type_width_and_signed(data_type, scope)
    return width, signed, packed_member_widths(data_type, scope)
