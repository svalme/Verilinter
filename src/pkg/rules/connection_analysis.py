from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..semantic.symbol import Symbol
from ..semantic.symbol_table import SymbolTable


def module_ports_for(symbol_table: SymbolTable, module_name: str | None) -> list[Symbol]:
    if not module_name:
        return []
    scope = symbol_table.lookup_module(module_name)
    if scope is None:
        return []
    return [symbol for symbol in scope.symbols.values() if symbol.is_port]


def module_scope_for(symbol_table: SymbolTable, module_name: str | None):
    if not module_name:
        return None
    return symbol_table.lookup_module(module_name)


def ordered_connections(instantiation: dict[str, object]) -> list[dict[str, object]]:
    return [
        conn
        for conn in instantiation.get("connections", [])
        if isinstance(conn, dict) and conn.get("kind") in {"ordered", "empty"}
    ]


def named_connections(instantiation: dict[str, object]) -> list[dict[str, object]]:
    return [
        conn
        for conn in instantiation.get("connections", [])
        if isinstance(conn, dict) and conn.get("kind") == "named"
    ]


def has_wildcard_port_connections(instantiation: dict[str, object]) -> bool:
    return any(
        isinstance(conn, dict) and conn.get("kind") == "wildcard"
        for conn in instantiation.get("connections", [])
    )


def has_ordered_port_connections(instantiation: dict[str, object]) -> bool:
    return any(
        isinstance(conn, dict) and conn.get("kind") == "ordered"
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
    if module_scope_for(symbol_table, instantiation.get("child_module")) is None:
        # Module isn't defined anywhere in the linted file set at all -- that's
        # UNDEFINED_MODULE's concern; there's no real port list to check named
        # connections against, so don't pile on a misleading "unknown port" per
        # connection on top of it.
        return []
    valid = {port.name for port in module_ports_for(symbol_table, instantiation.get("child_module"))}
    unknown: list[str] = []
    for conn in named_connections(instantiation):
        port_name = conn.get("port_name")
        if not isinstance(port_name, str):
            continue
        if port_name not in valid and port_name not in unknown:
            unknown.append(port_name)
    return unknown


def extra_ordered_connections(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[dict[str, object]]:
    """Return the trailing ordered/empty connections beyond the child module's
    declared port count.

    `bound_port_pairs` only ever zips as many connections as the module has ports
    (`enumerate(ports)`), so an instantiation with more positional connections than
    the module declares silently drops the extras from every check built on top of
    it (unconnected ports, width/signedness mismatch, unread output). This surfaces
    that dropped tail directly instead.
    """
    if module_scope_for(symbol_table, instantiation.get("child_module")) is None:
        return []
    ports = module_ports_for(symbol_table, instantiation.get("child_module"))
    ord_conns = ordered_connections(instantiation)
    if len(ord_conns) <= len(ports):
        return []
    return ord_conns[len(ports):]


def module_parameters_for(symbol_table: SymbolTable, module_name: str | None) -> list[Symbol]:
    if not module_name:
        return []
    scope = symbol_table.lookup_module(module_name)
    if scope is None:
        return []
    return [symbol for symbol in scope.symbols.values() if symbol.kind == "parameter"]


def named_parameter_overrides(instantiation: dict[str, object]) -> list[dict[str, object]]:
    return [
        p
        for p in instantiation.get("parameter_overrides", [])
        if isinstance(p, dict) and p.get("kind") == "named"
    ]


def has_ordered_parameter_overrides(instantiation: dict[str, object]) -> bool:
    return any(
        isinstance(override, dict) and override.get("kind") == "ordered"
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
    valid = {param.name for param in module_parameters_for(symbol_table, instantiation.get("child_module"))}
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
    names: list[str] = []
    for port, conn in bound_port_pairs(symbol_table, instantiation):
        if conn is None or conn.get("kind") == "empty" or conn.get("expr_text") is None:
            names.append(port.name)
    return names


def width_mismatch_details(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[tuple[str, int, str, int]]:
    mismatches: list[tuple[str, int, str, int]] = []
    for port, conn in bound_port_pairs(symbol_table, instantiation):
        if conn is None:
            continue
        conn_width = conn.get("expr_width")
        expr_text = conn.get("expr_text")
        if not isinstance(conn_width, int) or not isinstance(port.bit_width, int):
            continue
        if conn_width != port.bit_width:
            mismatches.append((port.name, port.bit_width, str(expr_text), conn_width))
    return mismatches


def width_unknown_details(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[tuple[str, int | None, str, int | None]]:
    unknowns: list[tuple[str, int | None, str, int | None]] = []
    for port, conn in bound_port_pairs(symbol_table, instantiation):
        if conn is None or conn.get("kind") == "empty":
            continue
        conn_width = conn.get("expr_width")
        expr_text = str(conn.get("expr_text") or "<open>")
        if isinstance(conn_width, int) and isinstance(port.bit_width, int):
            continue
        unknowns.append((port.name, port.bit_width, expr_text, conn_width))
    return unknowns


def signedness_mismatch_details(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> list[tuple[str, bool, str, bool]]:
    mismatches: list[tuple[str, bool, str, bool]] = []
    for port, conn in bound_port_pairs(symbol_table, instantiation):
        if conn is None:
            continue
        port_signed = port.is_signed
        expr_signed = conn.get("expr_signed")
        expr_text = conn.get("expr_text")
        if port_signed is None or expr_signed is None:
            continue
        if bool(port_signed) != bool(expr_signed):
            mismatches.append((port.name, bool(port_signed), str(expr_text), bool(expr_signed)))
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
        symbol = parent_scope.lookup(expr_name)
        if symbol is None:
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
    a real multi-driver conflict the walker can't see on its own: a
    port-connection expression is never visited by IdentifierNameHandler at all
    (HierarchyInstantiationHandler doesn't override `children()`, so the walker
    never descends into `.connections`), so the connected signal's `Symbol`
    carries zero UseEvents from the connection itself -- not "misclassified as a
    read", simply never walked."""
    conflicts: list[tuple[str, str]] = []
    parent_scope = module_scope_for(symbol_table, instantiation.get("parent_module"))
    if parent_scope is None:
        return conflicts

    for port, conn in bound_port_pairs(symbol_table, instantiation):
        if port.port_direction not in ("output", "inout") or conn is None or conn.get("kind") == "empty":
            continue
        expr_name = conn.get("expr_name")
        if not isinstance(expr_name, str):
            continue
        symbol = parent_scope.lookup(expr_name)
        if symbol is None or not symbol.is_written:
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
    `Symbol.is_written` at all -- port-connection expressions are never walked by
    `IdentifierNameHandler` (see `instance_output_driver_conflicts`'s docstring),
    so neither connection leaves any trace on `x`'s `Symbol`. This groups
    instantiations by parent module instead of relying on `Symbol` write state.

    Deliberately scoped to conflicts between *distinct* instances: one instance
    binding two of its own output ports to the same net (`u1(.out1(x), .out2(x))`)
    is a different, narrower bug shape and is left for a future rule rather than
    silently folded in here."""
    conflicts: list[tuple[dict[str, object], str, str, dict[str, object], str]] = []
    by_parent_module: dict[object, list[dict[str, object]]] = defaultdict(list)
    for inst in symbol_table.instantiations:
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
                prior = next(
                    (
                        (prior_inst, prior_port)
                        for prior_inst, prior_port in entries[:index]
                        if prior_inst is not inst
                    ),
                    None,
                )
                if prior is not None:
                    conflicts.append((inst, port_name, signal_name, prior[0], prior[1]))

    return conflicts
