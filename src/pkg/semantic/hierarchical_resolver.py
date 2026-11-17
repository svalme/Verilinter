"""Resolves a hierarchical path (`g.x`, `u.v.inner`, `top.p`, `$root.top.p`) to the symbol it names."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..parser.syntax import ROOT_PATH_SEGMENT
from .scope import Scope
from .scope_kinds import ScopeKind
from .symbol import Symbol

if TYPE_CHECKING:
    from .symbol_table import SymbolTable

_MAX_DEPTH = 64
_NAMED_BLOCK_KINDS = frozenset({ScopeKind.GENERATE_BLOCK, ScopeKind.BLOCK})


@dataclass(frozen=True)
class HierarchicalTarget:
    """The symbol a path ends at and the scope that declares it."""

    symbol: Symbol
    scope: Scope


class HierarchicalNameResolver:
    """Follows a path of scope names from the scope it is written in to the member it ends at.

    The first segment is looked up the way the language does it: a name visible from the scope (an
    instance or an interface port), then a generate or procedural block label in the scope or one
    around it, then a module name (an upward reference such as `top.p`); `$root` starts at a module
    name. Each later segment is a block label or an instance in the scope reached so far, and the
    member is looked up in that one scope only, so an outer name of the same spelling is never used.
    A step that cannot be followed (a struct variable, a name this table does not hold, an instance of a
    module that was not analysed) gives None. It reads the symbol table and never changes it.
    """

    def __init__(self, symbol_table: SymbolTable) -> None:
        self._table = symbol_table

    def resolve(self, from_scope: Scope, segments: list[str], member: str) -> HierarchicalTarget | None:
        if not segments:
            return None
        scope = self._first_scope(from_scope, segments)
        if scope is None:
            return None
        for segment in segments[2:] if segments[0] == ROOT_PATH_SEGMENT else segments[1:]:
            scope = self._enter(scope, segment)
            if scope is None:
                return None
        symbol = scope.lookup(member)
        return None if symbol is None else HierarchicalTarget(symbol, scope)

    def _first_scope(self, from_scope: Scope, segments: list[str]) -> Scope | None:
        first = segments[0]
        if first == ROOT_PATH_SEGMENT:
            return self._table.lookup_module(segments[1]) if len(segments) > 1 else None
        symbol = from_scope.lookup_hierarchical(first)
        if symbol is not None:
            return self._instance_scope(symbol)
        scope: Scope | None = from_scope
        for _ in range(_MAX_DEPTH):
            if scope is None:
                break
            found = self._named_child(scope, first)
            if found is not None:
                return found
            scope = scope.parent
        return self._table.lookup_module(first)

    def _enter(self, scope: Scope, segment: str) -> Scope | None:
        found = self._named_child(scope, segment)
        if found is not None:
            return found
        symbol = scope.lookup(segment)
        return None if symbol is None else self._instance_scope(symbol)

    def _instance_scope(self, symbol: Symbol) -> Scope | None:
        type_name = symbol.interface_type_name
        return None if type_name is None else self._table.lookup_module(type_name)

    def _named_child(self, scope: Scope, name: str, depth: int = 0) -> Scope | None:
        """A generate or procedural block labelled `name` directly in `scope`, looking through the
        unlabelled scope a loop generate opens around its body."""
        if depth >= _MAX_DEPTH:
            return None
        for child in scope.children:
            if child.name == name and child.kind in _NAMED_BLOCK_KINDS:
                return child
            if child.kind == ScopeKind.GENERATE_FOR and child.name is None:
                found = self._named_child(child, name, depth + 1)
                if found is not None:
                    return found
        return None
