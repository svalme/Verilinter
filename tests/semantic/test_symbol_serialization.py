from __future__ import annotations

from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_serialization import serialized_attributes, symbol_from_dict, symbol_to_dict

# A distinctive non-default value for every instance attribute of Symbol. The serializer takes its field
# list from the Symbol instance, so a new attribute is stored without editing it; this table makes the
# round-trip test exercise that attribute, and a missing entry fails the test below.
_SAMPLE_VALUES: dict[str, object] = {
    "name": "sig",
    "kind": "variable",
    "declarations": [{"line": 1, "col": 2}],
    "uses": [{"line": 3, "col": 4}],
    "use_events": [{"location": {"line": 3, "col": 4}, "read": True, "write": False}],
    "is_port": True,
    "is_function_return": True,
    "port_direction": "output",
    "bit_width": 12,
    "msb": 11,
    "lsb": 0,
    "is_signed": True,
    "value": 5,
    "is_constant": True,
    "is_localparam": True,
    "initializer_text": "8'hFF",
    "packed_dimensions": [("11", "0")],
    "packed_dimension_widths": [12],
    "unpacked_dimensions": [("3", "0")],
    "unpacked_dimension_widths": [4],
    "is_read": True,
    "is_written": True,
    "use_count": 4,
    "read_count": 3,
    "write_count": 1,
    "is_used_in_port_connection": True,
    "has_declaration_initializer": True,
    "is_event": True,
    "is_type_parameter": True,
    "interface_type_name": "data_t",
}

# Attributes that are rebuilt from the scope tree and not stored on the symbol itself.
_NOT_SERIALIZED = {"scope"}


def test_every_symbol_attribute_has_a_sample_value() -> None:
    attributes = set(vars(Symbol("sig", "variable"))) - _NOT_SERIALIZED
    assert attributes == set(_SAMPLE_VALUES), (
        "Symbol gained or lost an attribute; add a sample value for it in _SAMPLE_VALUES",
        attributes ^ set(_SAMPLE_VALUES),
    )


def test_serializer_stores_every_symbol_attribute() -> None:
    assert set(serialized_attributes()) == set(vars(Symbol("sig", "variable"))) - _NOT_SERIALIZED


def test_symbol_round_trips_every_attribute() -> None:
    symbol = Symbol("sig", "variable")
    for attribute, value in _SAMPLE_VALUES.items():
        setattr(symbol, attribute, value)

    restored = symbol_from_dict(symbol_to_dict(symbol))

    lost = [name for name, value in _SAMPLE_VALUES.items() if getattr(restored, name) != value]
    assert lost == [], f"attributes not preserved across serialization: {lost}"


def test_symbol_round_trips_through_json() -> None:
    import json

    symbol = Symbol("sig", "variable")
    for attribute, value in _SAMPLE_VALUES.items():
        setattr(symbol, attribute, value)

    restored = symbol_from_dict(json.loads(json.dumps(symbol_to_dict(symbol))))

    lost = [name for name, value in _SAMPLE_VALUES.items() if getattr(restored, name) != value]
    assert lost == [], f"attributes not preserved across a JSON round trip: {lost}"


def test_a_missing_field_keeps_the_symbol_default() -> None:
    restored = symbol_from_dict({"name": "sig", "kind": "variable"})

    assert restored.bit_width is None
    assert restored.use_events == []
    assert restored.is_port is False
