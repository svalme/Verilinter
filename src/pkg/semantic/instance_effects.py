"""What an instance's port connections do to the signals they name in the instantiating module.

The walk records a signal named in a port connection as a plain read, because the connected port's
direction is not known there. Once a file has been walked, each instance's child module is known (from the
file itself or from the corpus-wide port registry), so a connection to an output or inout port gives its
signal a write event owned by the instance, and a signal whose every port connection has a known direction
is no longer open to an unknown driver. The signal is looked up from the scope the instance sits in, so a
wire declared inside a generate block is the one found."""
from __future__ import annotations

from typing import NamedTuple

from .models import InstanceRecord, PortConnection
from .module_resolver import ModuleResolver, PortList
from .scope import Scope
from .symbol import Symbol
from .symbol_table import SymbolTable
from .write_region import WriteRegion

_DRIVING = ("output", "inout")

INSTANCE_DRIVER_PREFIX = "instance:"


def instance_driver_id(instance: InstanceRecord, port_name: str) -> str:
    """The driver id of the write an instance's output port makes: `instance:<file>:<line>:<col>:<name>:<port>`."""
    location = instance.location or {}
    return (
        f"{INSTANCE_DRIVER_PREFIX}{location.get('file', '')}:{location.get('line', 0)}:{location.get('col', 0)}"
        f":{instance.instance_name}:{port_name}"
    )


def is_instance_driver_id(driver_id: object) -> bool:
    return isinstance(driver_id, str) and driver_id.startswith(INSTANCE_DRIVER_PREFIX)


def instance_driver_parts(driver_id: str) -> tuple[str, str]:
    """`(instance name, port name)` of an instance driver id."""
    parts = driver_id.rsplit(":", 2)
    return (parts[-2], parts[-1]) if len(parts) == 3 else ("", "")


class _Connected(NamedTuple):
    """One signal a connection names: the symbol, the part of it the connection covers (empty for the whole
    symbol), the connected port's direction (None when unknown), whether the walk saw the connection's own
    identifier, the port name and the connection's location."""

    symbol: Symbol
    region: WriteRegion
    direction: str | None
    listed: bool
    port_name: str | None
    location: dict | None


def _expression_targets(conn: PortConnection, scope: Scope) -> list[tuple[Symbol, WriteRegion]]:
    """The signals a connection's expression names and the part of each: a simple name is the whole signal;
    a select (`bus[3]`, `bus[7:4]`, `s.field`) is that part; a concatenation is each of its members. An
    expression that is not a reference (`a & b`, a literal, a call) names none."""
    from ..parser.syntax import assignment_targets

    if isinstance(conn.expr_name, str):
        symbol = scope.lookup_hierarchical(conn.expr_name)
        return [(symbol, ())] if symbol is not None else []
    if conn.expr_node is None:
        return []
    return [
        (target.base_symbol, target.write_region)
        for target in assignment_targets(conn.expr_node, scope)
        if target.base_symbol is not None
    ]


def _connected_signals(instance: InstanceRecord, ports: PortList, scope: Scope) -> list[_Connected]:
    """Each signal the instance's connections name, with the port each is connected to. A `.*` connection
    supplies a signal of the port's own name for each port the list does not mention; `listed` is False for
    those, since the walk saw no identifier for them."""
    found: list[_Connected] = []
    named = {str(conn.get("port_name")) for conn in instance.connections if conn.get("kind") == "named"}
    directions = dict(ports)
    ordered_index = 0
    for conn in instance.connections:
        kind = conn.get("kind")
        if kind == "named":
            port_name = str(conn.get("port_name"))
            direction = directions.get(port_name)
        elif kind == "ordered":
            port_name = ports[ordered_index][0] if ordered_index < len(ports) else None
            direction = ports[ordered_index][1] if ordered_index < len(ports) else None
            ordered_index += 1
        elif kind == "wildcard":
            for name, port_direction in ports:
                symbol = scope.lookup_hierarchical(name) if name not in named else None
                if symbol is not None:
                    found.append(_Connected(symbol, (), port_direction, False, name, instance.location))
            continue
        else:
            continue
        found.extend(
            _Connected(symbol, region, direction, True, port_name, conn.get("location"))
            for symbol, region in _expression_targets(conn, scope)
        )
    return found


def _symbol_key(instance: InstanceRecord, symbol: Symbol) -> tuple[object, ...]:
    declaration = symbol.declarations[0] if symbol.declarations else {}
    return (instance.parent_module, symbol.name, tuple(sorted((k, str(v)) for k, v in declaration.items())))


def apply_instance_port_effects(symbol_table: SymbolTable) -> None:
    """Give each signal connected to an output or inout port a write event owned by the instance, and clear
    the open-driver mark on a signal whose every port connection has a known direction."""
    classified: dict[tuple[object, ...], tuple[Symbol, int]] = {}
    modules = ModuleResolver(symbol_table)
    for instance in symbol_table.instantiations:
        if instance.in_inactive_generate_branch:
            continue
        ports = modules.ports(instance.child_module)
        scope = instance.scope
        if scope is None:
            scope = modules.scope(instance.parent_module)
        if ports is None or scope is None:
            continue
        for connected in _connected_signals(instance, ports, scope):
            symbol, direction, port_name = connected.symbol, connected.direction, connected.port_name
            if direction is None:
                continue
            if direction in _DRIVING and port_name is not None:
                symbol.is_driven_by_instance = True
                symbol.add_use(
                    connected.location,
                    write=True,
                    driver_id=instance_driver_id(instance, port_name),
                    driver_location=instance.location,
                    branch_signature=instance.generate_branch_signature,
                    write_region=connected.region,
                )
            key = _symbol_key(instance, symbol)
            known, count = classified.get(key, (symbol, 0))
            classified[key] = (known, count + (1 if connected.listed else 0))

    for symbol, count in classified.values():
        wired = sum(1 for event in symbol.use_events if event.get("in_port_connection"))
        if wired == count:
            symbol.in_unclassified_port_connection = False


def release_walk_state(symbol_table: SymbolTable) -> None:
    """Drop what the instance effect needed only while the file was walked: the scope each instance sits in
    and the syntax node of each connection. A worker result keeps neither."""
    for instance in symbol_table.instantiations:
        instance.scope = None
        for conn in instance.connections:
            conn.expr_node = None
