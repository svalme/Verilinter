"""Converts a `Symbol` to and from a plain, JSON-safe dict.

This is the shape cached to SQLite and passed across the worker-process boundary. The fields come from the
`Symbol` instance itself, so an attribute added to `Symbol` is serialized without editing this module.
Scalars pass through; lists keep their dict elements as dicts and turn pair elements back into tuples
(a JSON round trip turns tuples into lists); `use_events` rebuild through `use_event_from_dict`.
"""
from __future__ import annotations

from typing import Any

from .symbol import Symbol, UseEvent
from .symbol_kind import SymbolKind

_PROTOTYPE = Symbol(name="", kind=SymbolKind.VARIABLE)
_CONSTRUCTOR_ATTRIBUTES = ("name", "kind")
# `scope` is the owning scope, rebuilt when the symbol is defined in one; it is not data about the symbol.
_NOT_SERIALIZED = frozenset({"scope"})
_ATTRIBUTES: tuple[str, ...] = tuple(
    attribute
    for attribute in vars(_PROTOTYPE)
    if attribute not in _NOT_SERIALIZED and attribute not in _CONSTRUCTOR_ATTRIBUTES
)


def serialized_attributes() -> tuple[str, ...]:
    """Every `Symbol` attribute that is stored, including `name` and `kind`."""
    return _CONSTRUCTOR_ATTRIBUTES + _ATTRIBUTES


def _dump_item(item: Any) -> Any:
    if isinstance(item, dict):
        return dict(item)
    if isinstance(item, tuple):
        return list(item)
    return item


def _load_item(item: Any) -> Any:
    if isinstance(item, dict):
        return dict(item)
    if isinstance(item, (list, tuple)):
        return tuple(item)
    return item


def use_event_from_dict(data: dict[str, Any]) -> UseEvent:
    """Reconstruct one `UseEvent` from its serialized dict, re-tupling
    `branch_signature`/`loop_ids` -- a JSON round-trip (the SQLite cache path)
    decays a tuple to a list, but callers compare/hash these as tuples."""
    event: UseEvent = {
        "location": data.get("location"),
        "read": bool(data.get("read", False)),
        "write": bool(data.get("write", False)),
    }
    driver_id = data.get("driver_id")
    if driver_id is not None:
        event["driver_id"] = str(driver_id)
    driver_location = data.get("driver_location")
    if driver_location is not None:
        event["driver_location"] = driver_location
    branch_signature = data.get("branch_signature")
    if branch_signature is not None:
        event["branch_signature"] = tuple(tuple(pair) for pair in branch_signature)
    statement_id = data.get("statement_id")
    if statement_id is not None:
        event["statement_id"] = str(statement_id)
    if data.get("in_port_connection"):
        event["in_port_connection"] = True
    if data.get("is_nonblocking_write"):
        event["is_nonblocking_write"] = True
    loop_ids = data.get("loop_ids")
    if loop_ids:
        event["loop_ids"] = tuple(loop_ids)
    return event


def symbol_to_dict(symbol: Symbol) -> dict[str, Any]:
    """Serialize a `Symbol`, including its full `use_events`; the counterpart to `symbol_from_dict`."""
    data: dict[str, Any] = {"name": symbol.name, "kind": str(symbol.kind)}
    for attribute in _ATTRIBUTES:
        value = getattr(symbol, attribute)
        if attribute == "use_events":
            data[attribute] = [dict(event) for event in value]
        elif isinstance(value, list):
            data[attribute] = [_dump_item(item) for item in value]
        else:
            data[attribute] = value
    return data


def symbol_from_dict(data: dict[str, Any]) -> Symbol:
    """Reconstruct a `Symbol` from `symbol_to_dict` output. A missing field keeps the `Symbol` default."""
    symbol = Symbol(name=str(data["name"]), kind=str(data.get("kind", "variable")))
    for attribute in _ATTRIBUTES:
        if attribute not in data:
            continue
        value = data[attribute]
        if attribute == "use_events":
            symbol.use_events = [use_event_from_dict(event) for event in value or [] if isinstance(event, dict)]
        elif isinstance(getattr(symbol, attribute), list):
            setattr(symbol, attribute, [_load_item(item) for item in value or []])
        else:
            setattr(symbol, attribute, value)
    return symbol
