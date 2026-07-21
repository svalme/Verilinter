# src/pkg/semantic/symbol_table.py
from __future__ import annotations

from ..vnodes.base_vnode import Location
from .symbol import Symbol
from .scope import Scope


class SymbolTable:
    """Manages multiple scopes and provides symbol lookup across the hierarchy."""

    def __init__(self) -> None:
        self.global_scope: Scope = Scope(kind="global")
        self.scopes: list[Scope] = [self.global_scope]  # registry - all scopes ever created
        self._scope_stack: list[Scope] = [self.global_scope]  # traversal stack
        self.modules: dict[str, list[Scope]] = {}  # module name -> all scopes defining it, across files
        self.module_references: list[tuple[str, Location]] = []
        self.current_file: str | None = None
        self._file_default_nettype_none: dict[str, bool] = {}

    def set_current_file(self, path: str) -> None:
        """Signal that a new file is about to be walked. Stamps all subsequent scopes."""
        self.current_file = path

    def set_current_file_default_nettype_none(self, enabled: bool) -> None:
        if self.current_file is None:
            raise RuntimeError("current_file must be set before default_nettype metadata")
        self._file_default_nettype_none[self.current_file] = enabled

    def current_file_uses_default_nettype_none(self) -> bool:
        if self.current_file is None:
            return False
        return self._file_default_nettype_none.get(self.current_file, False)

    def new_scope(
        self,
        kind: str,
        name: str | None = None,
        parent: Scope | None = None,
        location: Location | None = None,
    ) -> Scope:
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
            f"pop_scope called with only global scope on stack - "
            f"unbalanced push/pop in visitor (current: {self._scope_stack[-1]})"
        )
        self._scope_stack.pop()

    def register_module(self, name: str, scope: Scope) -> None:
        """Record a module definition. Appends if the name was already registered."""
        self.modules.setdefault(name, []).append(scope)

    def register_module_reference(self, name: str, location: Location) -> None:
        """Record an instantiation site referencing a module type by name."""
        self.module_references.append((name, location))

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

    def lookup_qualified(self, path: list[str]) -> Symbol | None:
        """Navigate scope tree by name path from global, then look up the final symbol.

        e.g. ["top", "sub", "clk"] -> navigate global->top->sub, look up "clk".
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
