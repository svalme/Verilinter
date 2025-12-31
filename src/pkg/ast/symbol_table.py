# src/pkg/ast/symbol_table.py
from ..vnode.base_vnode import Location

class Symbol:
    """Represents a declared symbol (variable, signal, etc.) in the design."""

    def __init__(self, name: str, kind: str):
        self.name = name
        self.kind = kind  # wire, reg, logic, variable, function, task
        self.scope: Scope | None = None

        self.declarations: list[Location] = []
        self.uses: list[Location] = []

        self.is_implicit: bool = False
        self.is_read: bool = False
        self.is_written: bool = False

    # delete this method later
    def set_scope(self, scope: Scope) -> None:
        self.scope = scope

    def add_declaration(self, loc: Location) -> None:
        self.declarations.append(loc)

    def add_use(self, loc: Location, read: bool = False, write: bool = False) -> None:
        self.uses.append(loc)
        self.is_read |= read
        self.is_written |= write

    @property
    def is_declared(self) -> bool:
        return bool(self.declarations)

class Scope:
    """Represents a scope (module, block, always block, etc.) containing symbols."""

    def __init__(self, kind: str, name: str | None = None):
        self.kind = kind  # module, always, block, function
        self.name = name
        self.symbols: dict[str, Symbol] = {}
        self.parent: Scope | None = None

    def set_parent(self, parent: Scope | None = None) -> None:
        self.parent = parent

    def define(self, symbol: Symbol) -> None:
        if symbol.name in self.symbols:
            # update the symbol if it's already in this scope
            pass
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Symbol | None:
        if name in self.symbols:
            return self.symbols[name]
        return None
    
    def __repr__(self) -> str:
        return f"Scope: kind={self.kind}, name={self.name} \nsymbols={list(self.symbols.keys())}"

class SymbolTable:
    """Manages multiple scopes and provides symbol lookup across the hierarchy."""

    def __init__(self):
        self.global_scope = Scope(kind="global")
        self.scopes: list[Scope] = [self.global_scope]

    def new_scope(
        self, kind: str, name: str | None = None, parent: Scope | None = None
    ) -> Scope:
        """Create a new nested scope."""
        parent = self.current_scope() 
        scope = Scope(kind=kind, name=name)
        scope.set_parent(parent)
        self.scopes.append(scope)
        return scope

    def current_scope(self) -> Scope | None:
        """Get the current (most recent) scope."""
        return self.scopes[-1] if self.scopes else None
    
    def add_scope(self, scope: Scope) -> None:
        if scope.parent is None:
            scope.set_parent(self.current_scope())
        self.scopes.append(scope)

    def lookup(self, name: str) -> Symbol | None:
        """Lookup a symbol by name, searching from the current scope upwards."""
        scope = self.current_scope()
        while scope:
            exists = scope.lookup(name)
            if exists:
                return exists
            scope = scope.parent
        return None
    
    def lookup_from_scope(self, name: str, scope: Scope | None = None) -> Symbol | None:
        """Lookup a symbol by name, starting from the given scope upwards."""
        if scope is None:
            return None
        while scope:
            exists = scope.lookup(name)
            if exists:
                return exists
            scope = scope.parent
        return None