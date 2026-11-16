"""One `ConnectionRecord` per port of each instance, built once after every file has been merged.

The records pair the child module's ports with what the instance connects to them, so a rule reads the pair
instead of matching names and positions itself. Named, positional, `.name` and `.*` connections are all
expanded here."""
from __future__ import annotations

from .expr_type import ExprType
from .instance_ports import instance_parameter_scope, module_scope_for, specialized_port_symbol
from .models import ConnectionRecord, InstanceRecord, PortConnection
from .symbol import Symbol
from .symbol_table import SymbolTable


def _child_ports(symbol_table: SymbolTable, instance: InstanceRecord) -> list[Symbol] | None:
    """The child's port symbols in declaration order, specialised by the instance's parameter overrides, or
    None when the child module is declared in no input file."""
    scope = module_scope_for(symbol_table, instance.child_module)
    if scope is None:
        return None
    ports = [symbol for symbol in scope.symbols.values() if symbol.is_port]
    parameters = instance_parameter_scope(symbol_table, instance)  # type: ignore[arg-type]
    return [specialized_port_symbol(port, parameters) for port in ports] if (parameters or parameters.unknown) else ports


def _record(
    instance: InstanceRecord,
    parent_scope: object,
    port_name: str | None,
    port: Symbol | None,
    connection: PortConnection | None,
    implicit: bool,
    child_known: bool = True,
) -> ConnectionRecord:
    expr_name = None
    expr_type = ExprType()
    if connection is not None:
        expr_name = connection.get("expr_name")
        expr_type = PortConnection.from_dict(connection).expr_type
    lookup = getattr(parent_scope, "lookup_hierarchical", None)
    signal = lookup(expr_name) if callable(lookup) and isinstance(expr_name, str) else None
    if implicit and signal is None and port_name is not None and callable(lookup):
        signal = lookup(port_name)
    if implicit and signal is not None:
        expr_type = ExprType(signal.whole_width, signal.is_signed)
    return ConnectionRecord(
        instance=instance,
        port_name=port_name,
        direction=port.port_direction if port is not None else None,
        port=port,
        connection=connection,
        signal=signal,
        port_width=port.whole_width if port is not None else None,
        port_signed=port.is_signed if port is not None else None,
        expr_type=expr_type,
        implicit=implicit,
        child_known=child_known,
    )


def build_connection_records(symbol_table: SymbolTable, instance: InstanceRecord) -> list[ConnectionRecord]:
    ports = _child_ports(symbol_table, instance)
    parent_scope = module_scope_for(symbol_table, instance.parent_module)
    records: list[ConnectionRecord] = []

    named = [conn for conn in instance.connections if conn.get("kind") == "named"]
    ordered = [conn for conn in instance.connections if conn.get("kind") in ("ordered", "empty")]
    use_named = instance.connection_style == "named"
    wildcard = any(conn.get("kind") == "wildcard" for conn in instance.connections)

    if ports is None:
        for conn in named:
            records.append(_record(instance, parent_scope, conn.get("port_name"), None, conn, False, child_known=False))
        for conn in ordered:
            records.append(_record(instance, parent_scope, None, None, conn, False, child_known=False))
        return records

    if use_named:
        by_port: dict[str, list[PortConnection]] = {}
        for conn in named:
            by_port.setdefault(str(conn.get("port_name")), []).append(conn)
        for port in ports:
            matched = by_port.pop(port.name, [])
            if not matched:
                records.append(_record(instance, parent_scope, port.name, port, None, wildcard))
            records.extend(_record(instance, parent_scope, port.name, port, conn, False) for conn in matched)
        for name, conns in by_port.items():
            records.extend(_record(instance, parent_scope, name, None, conn, False) for conn in conns)
        return records

    for index, port in enumerate(ports):
        conn = ordered[index] if index < len(ordered) else None
        records.append(_record(instance, parent_scope, port.name, port, conn, conn is None and wildcard))
    records.extend(_record(instance, parent_scope, None, None, conn, False) for conn in ordered[len(ports):])
    return records


def resolve_connections(symbol_table: SymbolTable) -> None:
    """Build the connection records of every instance in the table and keep them on the instance."""
    for instance in symbol_table.instantiations:
        instance.connection_records = build_connection_records(symbol_table, instance)


def connection_records_of(symbol_table: SymbolTable, instance: InstanceRecord | dict) -> list[ConnectionRecord]:
    """The connection records of an instance: the ones built after the merge, or, for an instance registered
    in a table that was never merged (a hand-built table), the ones the same builder gives now."""
    record_instance = InstanceRecord.from_dict(instance)
    if not record_instance.connection_records:
        record_instance.connection_records = build_connection_records(symbol_table, record_instance)
    return record_instance.connection_records
