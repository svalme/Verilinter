from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from ..parser.syntax import (
    evaluate_constant_text_expression,
    evaluate_packed_dimension_bounds,
    is_mutually_exclusive_branch_pair,
)
from .name_lookup import named_symbol
from ..semantic.models import ConnectionRecord, InstanceRecord, ParameterOverride, PortConnection
from ..semantic.instance_ports import (
    named_parameter_overrides,
    ordered_parameter_overrides,
)
from ..semantic.module_resolver import ModuleResolver
from ..semantic.connection_records import connection_records_of
from ..semantic.expr_type import WidthDetermination
from ..semantic.symbol_table import SymbolTable


def ordered_connections(instantiation: InstanceRecord | dict[str, object]) -> list[PortConnection | dict[str, object]]:
    return [
        conn
        for conn in instantiation.get("connections", [])
        if isinstance(conn, (PortConnection, Mapping, dict)) and conn.get("kind") in {"ordered", "empty"}
    ]


def named_connections(instantiation: InstanceRecord | dict[str, object]) -> list[PortConnection | dict[str, object]]:
    return [
        conn
        for conn in instantiation.get("connections", [])
        if isinstance(conn, (PortConnection, Mapping, dict)) and conn.get("kind") == "named"
    ]


def has_wildcard_port_connections(instantiation: InstanceRecord | dict[str, object]) -> bool:
    return any(
        isinstance(conn, (PortConnection, Mapping, dict)) and conn.get("kind") == "wildcard"
        for conn in instantiation.get("connections", [])
    )


def has_ordered_port_connections(instantiation: InstanceRecord | dict[str, object]) -> bool:
    return any(
        isinstance(conn, (PortConnection, Mapping, dict)) and conn.get("kind") == "ordered"
        for conn in instantiation.get("connections", [])
    )


def duplicate_named_port_names(instantiation: dict[str, object]) -> list[str]:
    duplicates: list[str] = []
    seen: set[str] = set()
    for conn in named_connections(instantiation):
        port_name = conn.get("port_name")
        if not isinstance(port_name, str):
            continue
        if port_name in seen and port_name not in duplicates:
            duplicates.append(port_name)
        seen.add(port_name)
    return duplicates


def unknown_named_port_names(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[str]:
    """The named connections whose port the child module does not have. A child declared in no input file
    is UNDEFINED_MODULE's concern, so it gives none."""
    unknown: list[str] = []
    for record in connection_records_of(symbol_table, instantiation):
        conn = record.connection
        if not record.child_known or conn is None or record.port is not None or conn.get("kind") != "named":
            continue
        port_name = conn.get("port_name")
        if isinstance(port_name, str) and port_name not in unknown:
            unknown.append(port_name)
    return unknown


def extra_ordered_connections(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[PortConnection]:
    """The trailing positional connections beyond the child module's declared port count."""
    return [
        record.connection
        for record in connection_records_of(symbol_table, instantiation)
        if record.child_known
        and record.port is None
        and record.connection is not None
        and record.connection.get("kind") in ("ordered", "empty")
    ]


def has_ordered_parameter_overrides(instantiation: InstanceRecord | dict[str, object]) -> bool:
    return any(
        isinstance(override, (ParameterOverride, Mapping, dict)) and override.get("kind") == "ordered"
        for override in instantiation.get("parameter_overrides", [])
    )


def duplicate_named_parameter_override_names(instantiation: dict[str, object]) -> list[str]:
    duplicates: list[str] = []
    seen: set[str] = set()
    for override in named_parameter_overrides(instantiation):
        name = override.get("param_name")
        if not isinstance(name, str):
            continue
        if name in seen and name not in duplicates:
            duplicates.append(name)
        seen.add(name)
    return duplicates


def unknown_named_parameter_override_names(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[str]:
    modules = ModuleResolver(symbol_table)
    child_module = instantiation.get("child_module")
    if modules.scope(child_module) is None:
        return []
    # A `parameter type t` name is overridable like a value parameter.
    valid = {param.name for param in modules.parameters(child_module, include_types=True)}
    unknown: list[str] = []
    for override in named_parameter_overrides(instantiation):
        name = override.get("param_name")
        if not isinstance(name, str):
            continue
        if name not in valid and name not in unknown:
            unknown.append(name)
    return unknown


def child_port_count(symbol_table: SymbolTable, instantiation: dict[str, object]) -> int:
    """How many ports the child module declares (0 when it is declared in no input file)."""
    return sum(1 for record in connection_records_of(symbol_table, instantiation) if record.port is not None)


def unconnected_port_names(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[str]:
    """The ports the instance leaves open: not listed, or listed with nothing in the parentheses. A port a
    `.*` connection may supply by name is not reported."""
    names: list[str] = []
    for record in connection_records_of(symbol_table, instantiation):
        if record.port is None or record.port_name is None:
            continue
        conn = record.connection
        if conn is None:
            left_open = not record.implicit
        else:
            left_open = _is_left_open(conn)
        if left_open and record.port_name not in names:
            names.append(record.port_name)
    return names


def _width_views(symbol_table: SymbolTable, instantiation: dict[str, object]) -> list[ConnectionRecord]:
    return [view for record in connection_records_of(symbol_table, instantiation) for view in record.width_views]


def width_mismatch_details(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[tuple[str, int, str, int]]:
    """`(port, port width, expression text, expression width)` for each connection whose two widths are
    known and differ. A `.*` connection compares the port with the signal of the same name. A connection that
    slang elaborated with different width pairs is judged on each pair, so a wrong instantiation is reported
    whatever the other instantiations do."""
    mismatches: list[tuple[str, int, str, int]] = []
    for record in _width_views(symbol_table, instantiation):
        if record.port is None:
            continue
        if record.connection is not None:
            expr_text = record.connection.get("expr_text")
        elif record.implicit and record.signal is not None:
            expr_text = record.signal.name
        else:
            continue
        if not isinstance(record.expr_width, int) or not isinstance(record.port_width, int):
            continue
        if record.expr_type.differs_from(record.port_width):
            mismatch = (record.port.name, record.port_width, str(expr_text), record.expr_width)
            if mismatch not in mismatches:
                mismatches.append(mismatch)
    return mismatches


def _typed_by_type_parameter(port: object) -> bool:
    """True when the port is declared with a type parameter (`input data_t d`), whose width no analysis can know."""
    type_name = getattr(port, "interface_type_name", None)
    symbol = named_symbol(getattr(port, "scope", None), type_name)
    return bool(getattr(symbol, "is_type_parameter", False))


def _is_left_open(conn: Mapping[str, object]) -> bool:
    """A connection with no expression: a positional empty slot, or a named `.p()`."""
    return conn.get("kind") == "empty" or conn.get("expr_text") is None


def width_unknown_details(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[tuple[str, int | None, str, int | None]]:
    unknowns: list[tuple[str, int | None, str, int | None]] = []
    for record in _width_views(symbol_table, instantiation):
        conn = record.connection
        if record.port is None or conn is None or _is_left_open(conn):
            continue
        if record.expr_type.determination is WidthDetermination.ADAPTS:
            continue
        if isinstance(record.expr_width, int) and isinstance(record.port_width, int):
            continue
        if record.port_width is None and _typed_by_type_parameter(record.port):
            continue
        unknown = (record.port.name, record.port_width, str(conn.get("expr_text") or "<open>"), record.expr_width)
        if unknown not in unknowns:
            unknowns.append(unknown)
    return unknowns


def signedness_mismatch_details(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[tuple[str, bool, str, bool]]:
    mismatches: list[tuple[str, bool, str, bool]] = []
    for record in connection_records_of(symbol_table, instantiation):
        conn = record.connection
        if record.port is None or conn is None:
            continue
        if record.port_signed is None or record.expr_signed is None:
            continue
        if bool(record.port_signed) != bool(record.expr_signed):
            mismatches.append((record.port.name, bool(record.port_signed), str(conn.get("expr_text")), bool(record.expr_signed)))
    return mismatches


def unread_instance_output_details(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[tuple[str, str]]:
    details: list[tuple[str, str]] = []
    parent_scope = ModuleResolver(symbol_table).scope(instantiation.get("parent_module"))
    if parent_scope is None:
        return details

    for record in connection_records_of(symbol_table, instantiation):
        port, conn = record.port, record.connection
        if port is None or port.port_direction != "output" or conn is None or conn.get("kind") == "empty":
            continue
        expr_name = conn.get("expr_name")
        if not isinstance(expr_name, str):
            continue
        symbol = named_symbol(parent_scope, expr_name)
        if symbol is None:
            continue
        if symbol.is_port and symbol.port_direction in ("output", "inout"):
            # The connected signal is itself the enclosing module's own output/
            # inout port -- forwarding an instance's output straight to a port is
            # the standard pass-through pattern (e.g. the last stage of a
            # pipeline), and "used outside this module" is exactly what a port
            # is for. There being no *further* local read is expected, not a
            # sign the driven value is thrown away.
            continue
        # Conservative first pass: only flag when the connected signal appears to
        # exist solely for this structural connection.
        if symbol.read_count <= 1:
            details.append((port.name, expr_name))
    return details


def signal_names_connected_to_instances(symbol_table: SymbolTable, parent_module: object) -> set[str]:
    """Return every simple-identifier signal name referenced in any port
    connection of an instantiation whose parent module is `parent_module`.

    Needed because a port-connection expression is never walked by
    `IdentifierNameHandler` at all (see `instance_output_driver_conflicts`'s
    docstring), so such a signal's own `Symbol` carries no trace of the
    connection -- this is the only way to tell "this net is wired to an
    instance" from existing data, used by `UNDRIVEN_TRISTATE_SIGNAL` to
    exclude a signal that something outside this module could legitimately
    drive or pull.
    """
    names: set[str] = set()
    for inst in symbol_table.instantiations:
        if inst.get("parent_module") != parent_module:
            continue
        for conn in inst.get("connections", []):
            if isinstance(conn, (PortConnection, Mapping, dict)):
                expr_name = conn.get("expr_name")
                if isinstance(expr_name, str):
                    names.add(expr_name)
    return names
