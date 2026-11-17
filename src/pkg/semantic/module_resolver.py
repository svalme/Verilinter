"""Answers what the symbol table knows about a module an instance names: its scope, ports and parameters."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .scope import Scope
from .symbol import Symbol
from .symbol_kind import SymbolKind

if TYPE_CHECKING:
    from .symbol_table import SymbolTable

PortList = list[tuple[str, str | None]]


class ModuleResolver:
    """Looks a module up by name, in the files analysed together first and then in the corpus-wide port
    registry that holds modules declared in files this run did not walk.

    A module found in a walked file has a scope, so its port symbols, widths and parameters are available.
    A module found only in the registry has port names and directions and nothing else: `ports` answers for
    it, `port_symbols` and `parameters` do not, so a width or a parameter is never guessed from a registry
    entry. A name that is neither is unknown, and `is_defined` says whether it is a primitive instead. It
    reads the symbol table and never changes it.
    """

    def __init__(self, symbol_table: SymbolTable) -> None:
        self._table = symbol_table

    def scope(self, name: str | None) -> Scope | None:
        """The scope of the module in a walked file, or None."""
        return self._table.lookup_module(name) if name else None

    def is_defined(self, name: str | None) -> bool:
        """The name is a module (walked or registered) or a user-defined primitive."""
        if not name:
            return False
        return self.scope(name) is not None or bool(self._table.module_ports.get(name)) or name in self._table.primitives

    def ports(self, name: str | None) -> PortList | None:
        """`(name, direction)` of each port in declaration order, or None when no module of that name is known."""
        scope = self.scope(name)
        if scope is not None:
            return [(symbol.name, symbol.port_direction) for symbol in scope.symbols.values() if symbol.is_port]
        entries = self._table.module_ports.get(name) if name else None
        if entries:
            return [(port["name"], port.get("direction")) for port in entries[0]["ports"]]
        return None

    def port_symbols(self, name: str | None) -> list[Symbol] | None:
        """The port symbols of a walked module in declaration order, or None when it has no scope."""
        scope = self.scope(name)
        if scope is None:
            return None
        return [symbol for symbol in scope.symbols.values() if symbol.is_port]

    def parameters(self, name: str | None, *, include_types: bool = False) -> list[Symbol]:
        """The parameter and localparam symbols of a walked module; `parameter type` names are included when asked for."""
        scope = self.scope(name)
        if scope is None:
            return []
        return [
            symbol
            for symbol in scope.symbols.values()
            if symbol.kind is SymbolKind.PARAMETER or (include_types and symbol.is_type_parameter)
        ]
