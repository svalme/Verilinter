"""What an instance's port connections do to the signals they name in the instantiating module.

The walk records a signal named in a port connection as a plain read, because the connected port's
direction is not known there. Once a file has been walked, each instance's child module is known (from the
file itself or from the corpus-wide port registry), so a connection to an output or inout port gives its
signal a write event owned by the instance, and a signal whose every port connection has a known direction
is no longer open to an unknown driver. The signal is looked up from the scope the instance sits in, so a
wire declared inside a generate block is the one found."""
from __future__ import annotations

from .models import InstanceRecord
from .symbol import Symbol
from .symbol_table import SymbolTable

_DRIVING = ("output", "inout")

INSTANCE_DRIVER_PREFIX = "instance:"

PortList = list[tuple[str, str | None]]


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


def _connected_names(
    instance: InstanceRecord, ports: PortList
) -> list[tuple[str, str | None, bool, str | None, dict | None]]:
    """`(signal name, port direction, listed, port name, location)` for each connection of the instance that
    names a simple signal. A `.*` connection supplies a signal of the port's own name for each port the list
    does not mention; `listed` is False for those, since the walk saw no identifier for them."""
    pairs: list[tuple[str, str | None, bool, str | None, dict | None]] = []
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
            pairs.extend(
                (name, port_direction, False, name, instance.location)
                for name, port_direction in ports
                if name not in named
            )
            continue
        else:
            continue
        expr_name = conn.get("expr_name")
        if isinstance(expr_name, str):
            pairs.append((expr_name, direction, True, port_name, conn.get("location")))
    return pairs


def _symbol_key(instance: InstanceRecord, symbol: Symbol) -> tuple[object, ...]:
    declaration = symbol.declarations[0] if symbol.declarations else {}
    return (instance.parent_module, symbol.name, tuple(sorted((k, str(v)) for k, v in declaration.items())))


def apply_instance_port_effects(symbol_table: SymbolTable) -> None:
    """Give each signal connected to an output or inout port a write event owned by the instance, and clear
    the open-driver mark on a signal whose every port connection has a known direction."""
    classified: dict[tuple[object, ...], tuple[Symbol, int]] = {}
    for instance in symbol_table.instantiations:
        if instance.in_inactive_generate_branch:
            continue
        ports = _child_ports(symbol_table, instance.child_module)
        scope = instance.scope
        if scope is None and instance.parent_module:
            scope = symbol_table.lookup_module(instance.parent_module)
        if ports is None or scope is None:
            continue
        for name, direction, listed, port_name, location in _connected_names(instance, ports):
            symbol = scope.lookup_hierarchical(name)
            if symbol is None or direction is None:
                continue
            if direction in _DRIVING and port_name is not None:
                symbol.is_driven_by_instance = True
                symbol.add_use(
                    location,
                    write=True,
                    driver_id=instance_driver_id(instance, port_name),
                    driver_location=instance.location,
                    branch_signature=instance.generate_branch_signature,
                )
            key = _symbol_key(instance, symbol)
            known, count = classified.get(key, (symbol, 0))
            classified[key] = (known, count + (1 if listed else 0))

    for symbol, count in classified.values():
        wired = sum(1 for event in symbol.use_events if event.get("in_port_connection"))
        if wired == count:
            symbol.in_unclassified_port_connection = False
