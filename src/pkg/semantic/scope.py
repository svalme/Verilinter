# src/pkg/semantic/scope.py
from __future__ import annotations

from ..vnodes.base_vnode import Location
from .scope_kinds import NAME_OWNING_SCOPE_KINDS, ScopeKind
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
        # (package_name, imported_name) pairs from `import pkg::*;`/`import pkg::name;`
        # statements appearing directly in this scope; `imported_name` is None for
        # the wildcard form. Consulted by SymbolTable.lookup_from_scope.
        self.imports: list[tuple[str, str | None]] = []
        # The symbol table's package registry (package name -> every scope declaring it), shared by
        # reference so an import resolves against packages declared in any file. None for a scope
        # built outside a symbol table.
        self.packages: dict[str, list[Scope]] | None = None
        self.fsm_models: list[object] = []
        # An `interface` definition: its signals are driven and read by the modules that connect to it.
        self.is_interface: bool = False
        # Set once a use of one of its members through a port or instance has been recorded in this file.
        self.has_visible_interface_users: bool = False

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
            existing.is_port |= symbol.is_port
            if symbol.bit_width is not None:
                existing.bit_width = symbol.bit_width
            if symbol.msb is not None:
                existing.msb = symbol.msb
            if symbol.lsb is not None:
                existing.lsb = symbol.lsb
            if symbol.is_signed is not None:
                existing.is_signed = symbol.is_signed
            if symbol.value is not None:
                existing.value = symbol.value
            existing.use_count += symbol.use_count
            existing.read_count += symbol.read_count
            existing.write_count += symbol.write_count
            if symbol.declarations:
                existing.kind = symbol.kind
            return

        symbol.scope = self
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Symbol | None:
        if name in self.symbols:
            return self.symbols[name]
        return None

    def lookup_hierarchical(self, name: str) -> Symbol | None:
        """The one name lookup: from this scope outward, then through imports.

        A declaration in this scope or an enclosing one always wins (ordinary shadowing), so the chain
        is walked to the end first. Only when that fails is the chain walked again for `import pkg::*;`
        and `import pkg::name;`, which resolve into the package's own scope."""
        current: Scope | None = self
        depth = 0
        while current is not None and depth < 64:
            depth += 1
            symbol = getattr(current, "lookup", lambda _n: None)(name)
            if symbol is not None:
                return symbol
            current = getattr(current, "parent", None)

        current = self
        depth = 0
        while current is not None and depth < 64:
            depth += 1
            for package_name, imported_name in current.imports:
                if imported_name is not None and imported_name != name:
                    continue
                found = self.lookup_package_member(package_name, name)
                if found is not None:
                    return found
            current = current.parent
        return None

    def lookup_package_member(self, package_name: str, name: str) -> Symbol | None:
        """`package_name::name`: the symbol the package declares, or None when the package or the name is
        not known to this scope's symbol table."""
        for package_scope in (self.packages or {}).get(package_name, ()):
            found = package_scope.lookup(name)
            if found is not None:
                return found
        return None

    def enclosing_interface(self) -> Scope | None:
        current: Scope | None = self
        depth = 0
        while current is not None and depth < 64:
            depth += 1
            if current.is_interface:
                return current
            current = current.parent
        return None

    def may_come_from_unseen_package(self, name: str) -> bool:
        """True when an `import pkg::*;` or `import pkg::name;` in this scope or an enclosing one could
        supply `name` from a package that no analysed file declares."""
        current: Scope | None = self
        depth = 0
        while current is not None and depth < 64:
            depth += 1
            for package_name, imported_name in current.imports:
                if imported_name in (None, name) and package_name not in (self.packages or {}):
                    return True
            current = current.parent
        return False

    def add_import(self, package_name: str, imported_name: str | None) -> None:
        self.imports.append((package_name, imported_name))

    def __repr__(self) -> str:
        return f"Scope: kind={self.kind}, name={self.name}, file={self.file} \nsymbols={list(self.symbols.keys())}"


def enclosing_name_owning_scope(scope: Scope) -> Scope:
    """The nearest enclosing module, package, subroutine or global scope (the scope itself when it is one)."""
    current: Scope | None = scope
    depth = 0
    while current is not None and depth < 64:
        depth += 1
        if current.kind in NAME_OWNING_SCOPE_KINDS:
            return current
        current = current.parent
    return scope


def enclosing_module_scope(scope: Scope | None) -> Scope | None:
    depth = 0
    while scope is not None and depth < 64:
        depth += 1
        if getattr(scope, "kind", None) == ScopeKind.MODULE:
            return scope
        scope = getattr(scope, "parent", None)
    return None


def enclosing_function_scope(scope: Scope | None) -> Scope | None:
    depth = 0
    while scope is not None and depth < 64:
        depth += 1
        if getattr(scope, "kind", None) == ScopeKind.FUNCTION:
            return scope
        scope = getattr(scope, "parent", None)
    return None
