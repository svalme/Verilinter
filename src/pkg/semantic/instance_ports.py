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


class ParameterScope(dict[str, int]):
    """Effective parameter values of an instance. `unknown` names the parameters the instance overrides with a
    value that cannot be evaluated: they have no known value, and the child's default no longer applies."""

    def __init__(self, values: Mapping[str, int] | None = None, unknown: frozenset[str] = frozenset()) -> None:
        super().__init__(values or {})
        self.unknown = frozenset(unknown)


def instance_parameter_scope(
    symbol_table: SymbolTable,
    instantiation: dict[str, object],
) -> ParameterScope:
    """Compute effective parameter values for an instance by merging child module default
    parameters with the instance's parameter overrides (named and ordered). Re-evaluates
    dependent parameters and localparams in declaration order."""
    from ..parser.syntax import constant_text_identifiers, evaluate_constant_text_expression

    child_module = instantiation.get("child_module")
    if not isinstance(child_module, str) or not child_module:
        return ParameterScope()
    child_scope = module_scope_for(symbol_table, child_module)
    if child_scope is None:
        return ParameterScope()

    child_params = [
        sym for sym in child_scope.symbols.values()
        if sym.kind is SymbolKind.PARAMETER
    ]
    if not child_params:
        return ParameterScope()

    overridable_params = [p for p in child_params if not getattr(p, "is_localparam", False)]

    effective: dict[str, int] = {}
    # A parameter the instance overrides with a value that cannot be evaluated has no known value: it must not
    # fall back to the child's default, which the override replaces.
    overridden_unknown: set[str] = set()
    for ov in named_parameter_overrides(instantiation):
        p_name = ov.get("param_name")
        val = ov.get("expr_value")
        if isinstance(p_name, str) and isinstance(val, int):
            effective[p_name] = val
        elif isinstance(p_name, str):
            overridden_unknown.add(p_name)

    for index, ov in enumerate(ordered_parameter_overrides(instantiation)):
        if index < len(overridable_params):
            val = ov.get("expr_value")
            if isinstance(val, int):
                effective[overridable_params[index].name] = val
            else:
                overridden_unknown.add(overridable_params[index].name)

    for param in child_params:
        if param.name in effective or param.name in overridden_unknown:
            continue
        init_text = getattr(param, "initializer_text", None)
        if init_text and overridden_unknown and constant_text_identifiers(init_text) & overridden_unknown:
            overridden_unknown.add(param.name)  # computed from a parameter whose value is unknown
            continue
        if init_text:
            folded = evaluate_constant_text_expression(init_text, scope=effective)
            if folded is not None:
                effective[param.name] = folded
                continue
        if param.value is not None:
            effective[param.name] = param.value

    return ParameterScope(effective, frozenset(overridden_unknown))


def specialized_port_symbol(port: Symbol, param_scope: dict[str, int]) -> Symbol:
    """Return a specialized copy of `port` whose bit_width and packed range (msb, lsb)
    are re-evaluated against the instance's effective parameter scope."""
    from ..parser.syntax import constant_text_identifiers, evaluate_packed_dimension_bounds

    packed_dims = getattr(port, "packed_dimensions", [])
    unknown_overrides = getattr(param_scope, "unknown", frozenset())
    if not packed_dims or not (param_scope or unknown_overrides):
        return port

    width, msb, lsb = evaluate_packed_dimension_bounds(packed_dims, scope=param_scope)
    if width is None:
        depends_on_unknown = any(
            constant_text_identifiers(text) & unknown_overrides for dimension in packed_dims for text in dimension
        )
        if not depends_on_unknown:
            return port
        # The width depends on a parameter the instance overrides with an unknown value: the child's default
        # no longer applies, so the width stays unknown.

    specialized = Symbol(name=port.name, kind=port.kind)
    specialized.is_port = port.is_port
    specialized.port_direction = port.port_direction
    specialized.is_signed = port.is_signed
    specialized.bit_width = width
    specialized.msb = msb
    specialized.lsb = lsb
    specialized.value = port.value
    specialized.packed_dimensions = port.packed_dimensions
    specialized.unpacked_dimensions = port.unpacked_dimensions
    specialized.unpacked_dimension_widths = port.unpacked_dimension_widths
    specialized.declarations = list(port.declarations)
    return specialized
