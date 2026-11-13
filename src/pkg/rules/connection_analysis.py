from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from ..parser.syntax import (
    evaluate_constant_text_expression,
    evaluate_packed_dimension_bounds,
    is_mutually_exclusive_branch_pair,
)
from ..semantic.models import InstanceRecord, ParameterOverride, PortConnection
from ..semantic.instance_ports import (
    instance_parameter_scope,
    module_ports_for,
    module_scope_for,
    named_parameter_overrides,
    ordered_parameter_overrides,
    specialized_port_symbol,
)
from ..semantic.connection_records import connection_records_of
from ..semantic.symbol import Symbol
from ..semantic.symbol_kind import SymbolKind
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


def module_parameters_for(symbol_table: SymbolTable, module_name: str | None) -> list[Symbol]:
    if not module_name:
        return []
    scope = symbol_table.lookup_module(module_name)
    if scope is None:
        return []
    return [symbol for symbol in scope.symbols.values() if symbol.kind is SymbolKind.PARAMETER]


def module_type_parameters_for(symbol_table: SymbolTable, module_name: str | None) -> list[Symbol]:
    """The `parameter type t` names of a module; they are overridable like value parameters."""
    scope = symbol_table.lookup_module(module_name) if module_name else None
    if scope is None:
        return []
    return [symbol for symbol in scope.symbols.values() if symbol.is_type_parameter]


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
    if module_scope_for(symbol_table, instantiation.get("child_module")) is None:
        return []
    child_module = instantiation.get("child_module")
    valid = {param.name for param in module_parameters_for(symbol_table, child_module)}
    valid |= {param.name for param in module_type_parameters_for(symbol_table, child_module)}
    unknown: list[str] = []
    for override in named_parameter_overrides(instantiation):
        name = override.get("param_name")
        if not isinstance(name, str):
            continue
        if name not in valid and name not in unknown:
            unknown.append(name)
    return unknown


def bound_port_pairs(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[tuple[Symbol, dict[str, object] | None]]:
    if has_wildcard_port_connections(instantiation):
        # `.*` is an implicit binding form; this first-pass connection analysis
        # only reasons about explicit named / ordered entries. Don't invent a
        # fake port map here and cascade misleading correctness diagnostics.
        return []
    ports = module_ports_for(symbol_table, instantiation.get("child_module"))
    param_scope = instance_parameter_scope(symbol_table, instantiation)
    if param_scope:
        ports = [specialized_port_symbol(port, param_scope) for port in ports]

    style = instantiation.get("connection_style")

    if style == "named":
        conn_map = {
            str(conn.get("port_name")): conn
            for conn in named_connections(instantiation)
            if conn.get("port_name") is not None
        }
        return [(port, conn_map.get(port.name)) for port in ports]

    ord_conns = ordered_connections(instantiation)
    return [
        (port, ord_conns[index] if index < len(ord_conns) else None)
        for index, port in enumerate(ports)
    ]


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
            left_open = conn.get("kind") == "empty" or conn.get("expr_text") is None
        if left_open and record.port_name not in names:
            names.append(record.port_name)
    return names


def width_mismatch_details(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[tuple[str, int, str, int]]:
    """`(port, port width, expression text, expression width)` for each connection whose two widths are
    known and differ. A `.*` connection compares the port with the signal of the same name."""
    mismatches: list[tuple[str, int, str, int]] = []
    for record in connection_records_of(symbol_table, instantiation):
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
        if record.expr_width != record.port_width:
            mismatches.append((record.port.name, record.port_width, str(expr_text), record.expr_width))
    return mismatches


def _typed_by_type_parameter(port: object) -> bool:
    """True when the port is declared with a type parameter (`input data_t d`), whose width no analysis can know."""
    type_name = getattr(port, "interface_type_name", None)
    lookup = getattr(getattr(port, "scope", None), "lookup_hierarchical", None)
    symbol = lookup(type_name) if type_name and callable(lookup) else None
    return bool(getattr(symbol, "is_type_parameter", False))


def width_unknown_details(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[tuple[str, int | None, str, int | None]]:
    unknowns: list[tuple[str, int | None, str, int | None]] = []
    for record in connection_records_of(symbol_table, instantiation):
        conn = record.connection
        if record.port is None or conn is None or conn.get("kind") == "empty":
            continue
        if isinstance(record.expr_width, int) and isinstance(record.port_width, int):
            continue
        if record.port_width is None and _typed_by_type_parameter(record.port):
            continue
        unknowns.append((record.port.name, record.port_width, str(conn.get("expr_text") or "<open>"), record.expr_width))
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
    parent_scope = module_scope_for(symbol_table, instantiation.get("parent_module"))
    if parent_scope is None:
        return details

    for port, conn in bound_port_pairs(symbol_table, instantiation):
        if port.port_direction != "output" or conn is None or conn.get("kind") == "empty":
            continue
        expr_name = conn.get("expr_name")
        if not isinstance(expr_name, str):
            continue
        symbol = parent_scope.lookup_hierarchical(expr_name)
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
        if symbol.use_count <= 1:
            details.append((port.name, expr_name))
    return details


def instance_output_driver_conflicts(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[tuple[str, str]]:
    """Return (port_name, signal_name) pairs where an instance's output/inout
    port is connected to a parent-scope signal that already has an independent
    write elsewhere in the parent module (an `assign` or a procedural write) --
    a real multi-driver conflict the walker can't see on its own: an identifier
    used inside a port-connection expression is always recorded as a plain
    read regardless of which side of the connection actually drives the net
    (see `enclosing_port_connection`'s docstring), so this connection's own
    contribution never sets the connected signal's `Symbol.is_written` -- only
    an independent write elsewhere does, which is exactly the case this
    function is checking for."""
    conflicts: list[tuple[str, str]] = []
    parent_scope = module_scope_for(symbol_table, instantiation.get("parent_module"))
    if parent_scope is None:
        return conflicts

    inst_signature = instantiation.get("generate_branch_signature", ())
    for port, conn in bound_port_pairs(symbol_table, instantiation):
        if port.port_direction not in ("output", "inout") or conn is None or conn.get("kind") == "empty":
            continue
        expr_name = conn.get("expr_name")
        if not isinstance(expr_name, str):
            continue
        symbol = parent_scope.lookup_hierarchical(expr_name)
        if symbol is None or not symbol.is_written:
            continue
        # A write confined to a `generate if`/`else` branch mutually exclusive with
        # this instantiation's own branch (see branch_exclusivity_signature) can
        # never coexist with this connection, so it is not a real conflict. Only
        # skip when *every* write is exclusive with this instance; a genuine
        # co-existing write anywhere still flags.
        write_events = [event for event in symbol.use_events if event["write"]]
        if write_events and all(
            is_mutually_exclusive_branch_pair(inst_signature, event.get("branch_signature", ()))
            for event in write_events
        ):
            continue
        conflicts.append((port.name, expr_name))
    return conflicts


def multiple_instance_driver_conflicts(
    symbol_table: SymbolTable,
) -> list[tuple[dict[str, object], str, str, dict[str, object], str]]:
    """Return (instance, port_name, signal_name, first_instance, first_port_name)
    tuples where two or more instantiations in the same parent module bind their
    own `output`/`inout` ports to the same parent-scope signal.

    `instance_output_driver_conflicts` only catches an instance output colliding
    with an `assign` or procedural write on the same signal, because it relies on
    `Symbol.is_written`. Two instances that both drive a net purely through their
    own output ports (`sub1 u1(.out(x)); sub2 u2(.out(x));`) never touch
    `Symbol.is_written` at all -- each connection's own identifier is recorded as
    a plain read, never a write (see `instance_output_driver_conflicts`'s
    docstring), so neither connection leaves a write trace on `x`'s `Symbol`,
    even though both do leave a (read) trace. This groups
    instantiations by parent module instead of relying on `Symbol` write state.

    Deliberately scoped to conflicts between *distinct* instances: one instance
    binding two of its own output ports to the same net (`u1(.out1(x), .out2(x))`)
    is a different, narrower bug shape and is left for a future rule rather than
    silently folded in here."""
    conflicts: list[tuple[dict[str, object], str, str, dict[str, object], str]] = []
    by_parent_module: dict[object, list[dict[str, object]]] = defaultdict(list)
    for inst in symbol_table.instantiations:
        if inst.get("in_inactive_generate_branch"):
            continue
        by_parent_module[inst.get("parent_module")].append(inst)

    for parent_module, instantiations in by_parent_module.items():
        if parent_module is None:
            continue
        drivers: dict[str, list[tuple[dict[str, object], str]]] = defaultdict(list)
        for inst in instantiations:
            for port, conn in bound_port_pairs(symbol_table, inst):
                if port.port_direction not in ("output", "inout") or conn is None or conn.get("kind") == "empty":
                    continue
                expr_name = conn.get("expr_name")
                if not isinstance(expr_name, str):
                    continue
                drivers[expr_name].append((inst, port.name))

        for signal_name, entries in drivers.items():
            for index, (inst, port_name) in enumerate(entries):
                inst_signature = inst.get("generate_branch_signature", ())
                prior = next(
                    (
                        (prior_inst, prior_port)
                        for prior_inst, prior_port in entries[:index]
                        if prior_inst is not inst
                        and not is_mutually_exclusive_branch_pair(
                            inst_signature, prior_inst.get("generate_branch_signature", ())
                        )
                    ),
                    None,
                )
                if prior is not None:
                    conflicts.append((inst, port_name, signal_name, prior[0], prior[1]))

    return conflicts


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
