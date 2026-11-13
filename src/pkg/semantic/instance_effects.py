"""What an instance's port connections do to the signals they name in the instantiating module.

The walk records a signal named in a port connection as a plain read, because the connected port's
direction is not known there. Once a file has been walked, each instance's child module is known (from the
file itself or from the corpus-wide port registry), so a connection to an output or inout port marks its
signal as driven by the instance, and a signal whose every port connection has a known direction is no
longer open to an unknown driver.
"""
from __future__ import annotations

from .models import InstanceRecord
from .symbol import Symbol
from .symbol_table import SymbolTable

_DRIVING = ("output", "inout")

PortList = list[tuple[str, str | None]]


def _child_ports(symbol_table: SymbolTable, child_module: str | None) -> PortList | None:
    """`(name, direction)` of each port of the child module in declaration order, or None when it is unknown."""
    if not child_module:
        return None
    scope = symbol_table.lookup_module(child_module)
    if scope is not None:
        return [(symbol.name, symbol.port_direction) for symbol in scope.symbols.values() if symbol.is_port]
    entries = symbol_table.module_ports.get(child_module)
    if entries:
        return [(port["name"], port.get("direction")) for port in entries[0]["ports"]]
    return None


def _connected_names(instance: InstanceRecord, ports: PortList) -> list[tuple[str, str | None, bool]]:
    """`(signal name, port direction, listed)` for each connection of the instance that names a simple
    signal. A `.*` connection supplies a signal of the port's own name for each port the list does not
    mention; `listed` is False for those, since the walk saw no identifier for them."""
    pairs: list[tuple[str, str | None, bool]] = []
    named = {str(conn.get("port_name")) for conn in instance.connections if conn.get("kind") == "named"}
    directions = dict(ports)
    ordered_index = 0
    for conn in instance.connections:
        kind = conn.get("kind")
        if kind == "named":
            direction = directions.get(str(conn.get("port_name")))
        elif kind == "ordered":
            direction = ports[ordered_index][1] if ordered_index < len(ports) else None
            ordered_index += 1
        elif kind == "wildcard":
            pairs.extend((name, port_direction, False) for name, port_direction in ports if name not in named)
            continue
        else:
            continue
        expr_name = conn.get("expr_name")
        if isinstance(expr_name, str):
            pairs.append((expr_name, direction, True))
    return pairs


def apply_instance_port_effects(symbol_table: SymbolTable) -> None:
    """Mark each signal connected to an output or inout port as driven by an instance, and clear the
    open-driver mark on a signal whose every port connection has a known direction."""
    classified: dict[tuple[str | None, str], tuple[Symbol, int]] = {}
    for instance in symbol_table.instantiations:
        if instance.in_inactive_generate_branch:
            continue
        ports = _child_ports(symbol_table, instance.child_module)
        parent_scope = symbol_table.lookup_module(instance.parent_module) if instance.parent_module else None
        if ports is None or parent_scope is None:
            continue
        for name, direction, listed in _connected_names(instance, ports):
            symbol = parent_scope.lookup_hierarchical(name)
            if symbol is None or direction is None:
                continue
            if direction in _DRIVING:
                symbol.is_driven_by_instance = True
            key = (instance.parent_module, symbol.name)
            known, count = classified.get(key, (symbol, 0))
            classified[key] = (known, count + (1 if listed else 0))

    for symbol, count in classified.values():
        wired = sum(1 for event in symbol.use_events if event.get("in_port_connection"))
        if wired == count:
            symbol.in_unclassified_port_connection = False
