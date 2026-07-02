# src/pkg/ast/symbol_table.py
from ..vnodes.base_vnode import Location

class Symbol:
    """Represents a declared symbol (variable, signal, etc.) in the design."""

    def __init__(self, name: str, kind: str):
        self.name = name
        self.kind = kind  # wire, reg, logic, variable, function, task
        self.scope: "Scope | None" = None

        self.declarations: list[Location] = []
        self.uses: list[Location] = []

        self.is_implicit: bool = False
        self.is_read: bool = False
        self.is_written: bool = False

    def set_scope(self, scope: "Scope | None") -> None:
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

    def __init__(self, kind: str, name: str | None = None, location: Location | None = None):
        self.kind = kind  # module, always, block, function
        self.name = name
        self.file: str | None = None
        self.location = location  # where the scope-opening construct (e.g. module header) was declared
        self.symbols: dict[str, Symbol] = {}
        self.parent: "Scope | None" = None
        self.children: list["Scope"] = []

    def set_parent(self, parent: "Scope | None" = None) -> None:
        self.parent = parent
        if parent is not None and self not in parent.children:
            parent.children.append(self)

    def define(self, symbol: Symbol) -> None:
        if symbol.name in self.symbols:
            existing = self.symbols[symbol.name]
            existing.declarations.extend(symbol.declarations)
            existing.uses.extend(symbol.uses)
            existing.is_read |= symbol.is_read
            existing.is_written |= symbol.is_written
            if symbol.declarations:
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

class SymbolTable:
    """Manages multiple scopes and provides symbol lookup across the hierarchy."""

    def __init__(self):
        self.global_scope = Scope(kind="global")
        self.scopes: list[Scope] = [self.global_scope]   # registry — all scopes ever created
        self._scope_stack: list[Scope] = [self.global_scope]  # traversal stack
        self.modules: dict[str, list[Scope]] = {}  # module name → all scopes defining it, across files
        self.current_file: str | None = None

    def set_current_file(self, path: str) -> None:
        """Signal that a new file is about to be walked. Stamps all subsequent scopes."""
        self.current_file = path

    def add_scope(self, scope: Scope) -> None:
        """Add an existing scope to the registry and push it onto the traversal stack."""
        if scope.parent is None and self._scope_stack:
            scope.set_parent(self._scope_stack[-1])
        scope.file = self.current_file
        if scope not in self.scopes:
            self.scopes.append(scope)
        self._scope_stack.append(scope)

    def new_scope(self, kind: str, name: str | None = None, parent: Scope | None = None, location: Location | None = None) -> Scope:
        """Create a new scope, add it to the registry, and push it onto the traversal stack."""
        if parent is None:
            parent = self._scope_stack[-1] if self._scope_stack else None

        scope = Scope(kind=kind, name=name, location=location)
        scope.file = self.current_file
        scope.set_parent(parent)
        self.scopes.append(scope)
        self._scope_stack.append(scope)
        return scope

    def pop_scope(self) -> None:
        """Exit the current scope, returning to the parent."""
        assert len(self._scope_stack) > 1, (
            f"pop_scope called with only global scope on stack — "
            f"unbalanced push/pop in visitor (current: {self._scope_stack[-1]})"
        )
        self._scope_stack.pop()

    def current_scope(self) -> Scope | None:
        return self._scope_stack[-1] if self._scope_stack else None

    def lookup(self, name: str) -> Symbol | None:
        """Lookup a symbol starting from the current traversal scope upwards."""
        return self.lookup_from_scope(name, self.current_scope())

    def register_module(self, name: str, scope: Scope) -> None:
        """Record a module definition. Appends if the name was already registered (duplicate module)."""
        self.modules.setdefault(name, []).append(scope)

    def lookup_module(self, name: str) -> Scope | None:
        """Return the first scope for a named module, or None if not yet seen."""
        scopes = self.modules.get(name)
        return scopes[0] if scopes else None

    def is_duplicate_module(self, name: str) -> bool:
        """Return True if more than one file defines a module with this name."""
        return len(self.modules.get(name, [])) > 1

    def lookup_from_scope(self, name: str, scope: Scope | None = None) -> Symbol | None:
        """Lookup a symbol starting from the given scope upwards."""
        if scope is None:
            return None
        while scope:
            exists = scope.lookup(name)
            if exists:
                return exists
            scope = scope.parent
        return None

    def lookup_downward(self, name: str, from_scope: Scope | None = None) -> Symbol | None:
        """BFS through children of from_scope (or current scope) for a symbol."""
        root = from_scope if from_scope is not None else self.current_scope()
        if root is None:
            return None
        queue = list(root.children)
        while queue:
            child = queue.pop(0)
            found = child.lookup(name)
            if found:
                return found
            queue.extend(child.children)
        return None

    def lookup_sibling(self, name: str, from_scope: Scope | None = None) -> Symbol | None:
        """Search symbols in sibling scopes (same parent, not self)."""
        scope = from_scope if from_scope is not None else self.current_scope()
        if scope is None or scope.parent is None:
            return None
        for sibling in scope.parent.children:
            if sibling is scope:
                continue
            found = sibling.lookup(name)
            if found:
                return found
        return None

    def lookup_qualified(self, path: list[str]) -> Symbol | None:
        """Navigate scope tree by name path from global, then look up the final symbol.

        e.g. ["top", "sub", "clk"] → navigate global→top→sub, look up "clk".
        """
        if not path:
            return None
        current: Scope | None = self.global_scope
        for segment in path[:-1]:
            current = next((c for c in current.children if c.name == segment), None)
            if current is None:
                return None
        return current.lookup(path[-1])

    def lookup_global(self, name: str) -> Symbol | None:
        """DFS from global scope through the entire scope tree."""
        def _search(scope: Scope) -> Symbol | None:
            found = scope.lookup(name)
            if found:
                return found
            for child in scope.children:
                found = _search(child)
                if found:
                    return found
            return None
        return _search(self.global_scope)