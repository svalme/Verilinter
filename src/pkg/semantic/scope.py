# src/pkg/semantic/scope.py
from __future__ import annotations

from ..vnodes.base_vnode import Location
from .symbol import Symbol

class Scope:
    """Represents a scope (module, block, always block, etc.) containing symbols."""

    def __init__(self, kind: str, name: str | None = None, location: Location | None = None) -> None:
        self.kind = kind  # module, always, block, function
        self.name = name
        self.file: str | None = None
        self.location = location  # where the scope-opening construct (e.g. module header) was declared
        self.symbols: dict[str, Symbol] = {}
        self.parent: Scope | None = None
        self.children: list[Scope] = []

    def set_parent(self, parent: Scope | None = None) -> None:
        self.parent = parent
        if parent is not None and self not in parent.children:
            parent.children.append(self)

    def define(self, symbol: Symbol) -> None:
        if symbol.name in self.symbols:
            existing = self.symbols[symbol.name]
            existing.declarations.extend(symbol.declarations)
            existing.uses.extend(symbol.uses)
            existing.use_events.extend(symbol.use_events)
            existing.is_read |= symbol.is_read
            existing.is_written |= symbol.is_written
            if symbol.declarations:
                existing.kind = symbol.kind
                existing.is_implicit = False
            return

        symbol.scope = self
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Symbol | None:
        if name in self.symbols:
            return self.symbols[name]
        return None

    def __repr__(self) -> str:
        return f"Scope: kind={self.kind}, name={self.name}, file={self.file} \nsymbols={list(self.symbols.keys())}"
