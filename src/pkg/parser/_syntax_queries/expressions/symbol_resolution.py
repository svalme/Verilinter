"""The name lookup the expression evaluators use (`LOOKUP_REGISTER.md` L10): a scope, a name-to-int mapping or any object with `lookup_hierarchical`."""
from __future__ import annotations

from collections.abc import Mapping
from ..shared import identifier_name
from .operand_shapes import unwrap_parentheses


def resolve_symbol_in_scope(scope: object, name: str) -> object:
    if scope is None or not name:
        return None
    if isinstance(scope, Mapping):
        if name in scope:
            val = scope[name]
            if isinstance(val, int):
                from types import SimpleNamespace
                return SimpleNamespace(value=val)
            return val
        return None
    lookup_hierarchical = getattr(scope, "lookup_hierarchical", None)
    if callable(lookup_hierarchical):
        return lookup_hierarchical(name)
    current = scope
    depth = 0
    seen: set[int] = set()
    while current is not None and depth < 64:
        cid = id(current)
        if cid in seen:
            break
        seen.add(cid)
        depth += 1
        symbol = getattr(current, "lookup", lambda _name: None)(name)
        if symbol is not None:
            return symbol
        current = getattr(current, "parent", None)
    return None


def resolve_package_member_in_scope(scope: object, package_name: str, name: str) -> object:
    """`package_name::name` as the symbol the package declares, or None when the scope cannot see the package."""
    lookup_package_member = getattr(scope, "lookup_package_member", None)
    if callable(lookup_package_member):
        return lookup_package_member(package_name, name)
    return None


def is_constant_symbol_operand(scope: object, expr: object) -> bool:
    """True for a name that resolves to a parameter, localparam or enum member."""
    symbol = resolve_symbol_in_scope(scope, identifier_name(unwrap_parentheses(expr)) or "")
    return bool(getattr(symbol, "is_compile_time_constant", False))
