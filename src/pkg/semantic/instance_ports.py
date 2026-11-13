"""The ports and parameters of an instance's child module, as the instance sees them.

Shared by the connection rules and the connection records: which module an instance names, its ports in
declaration order, and the parameter values the instance's overrides give the child, from which a port's
width is re-evaluated."""
from __future__ import annotations

from collections.abc import Mapping

from .models import InstanceRecord, ParameterOverride
from .symbol import Symbol
from .symbol_kind import SymbolKind
from .symbol_table import SymbolTable


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


def named_parameter_overrides(instantiation: InstanceRecord | dict[str, object]) -> list[ParameterOverride | dict[str, object]]:
    return [
        p
        for p in instantiation.get("parameter_overrides", [])
        if isinstance(p, (ParameterOverride, Mapping, dict)) and p.get("kind") == "named"
    ]


def ordered_parameter_overrides(
    instantiation: InstanceRecord | dict[str, object],
) -> list[ParameterOverride | dict[str, object]]:
    return [
        p
        for p in instantiation.get("parameter_overrides", [])
        if isinstance(p, (ParameterOverride, Mapping, dict)) and p.get("kind") == "ordered"
    ]


def instance_parameter_scope(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> dict[str, int]:
    """Compute effective parameter values for an instance by merging child module default
    parameters with the instance's parameter overrides (named and ordered). Re-evaluates
    dependent parameters and localparams in declaration order."""
    from ..parser.syntax import evaluate_constant_text_expression

    child_module = instantiation.get("child_module")
    if not isinstance(child_module, str) or not child_module:
        return {}
    child_scope = module_scope_for(symbol_table, child_module)
    if child_scope is None:
        return {}

    child_params = [
        sym for sym in child_scope.symbols.values()
        if sym.kind is SymbolKind.PARAMETER
    ]
    if not child_params:
        return {}

    overridable_params = [p for p in child_params if not getattr(p, "is_localparam", False)]

    effective: dict[str, int] = {}
    for ov in named_parameter_overrides(instantiation):
        p_name = ov.get("param_name")
        val = ov.get("expr_value")
        if isinstance(p_name, str) and isinstance(val, int):
            effective[p_name] = val

    for index, ov in enumerate(ordered_parameter_overrides(instantiation)):
        if index < len(overridable_params):
            val = ov.get("expr_value")
            if isinstance(val, int):
                effective[overridable_params[index].name] = val

    for param in child_params:
        if param.name in effective:
            continue
        init_text = getattr(param, "initializer_text", None)
        if init_text:
            folded = evaluate_constant_text_expression(init_text, scope=effective)
            if folded is not None:
                effective[param.name] = folded
                continue
        if param.value is not None:
            effective[param.name] = param.value

    return effective


def specialized_port_symbol(port: Symbol, param_scope: dict[str, int]) -> Symbol:
    """Return a specialized copy of `port` whose bit_width and packed range (msb, lsb)
    are re-evaluated against the instance's effective parameter scope."""
    from ..parser.syntax import evaluate_packed_dimension_bounds

    packed_dims = getattr(port, "packed_dimensions", [])
    if not param_scope or not packed_dims:
        return port

    width, msb, lsb = evaluate_packed_dimension_bounds(packed_dims, scope=param_scope)
    if width is None:
        return port

    specialized = Symbol(name=port.name, kind=port.kind)
    specialized.is_port = port.is_port
    specialized.port_direction = port.port_direction
    specialized.is_signed = port.is_signed
    specialized.bit_width = width
    specialized.msb = msb
    specialized.lsb = lsb
    specialized.value = port.value
    specialized.packed_dimensions = port.packed_dimensions
    specialized.declarations = list(port.declarations)
    return specialized
