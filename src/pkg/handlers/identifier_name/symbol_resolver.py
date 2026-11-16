from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from ...parser.syntax import is_hierarchical_path_base, scoped_name_package_qualifier
from ...semantic.resolution import Resolution, ResolutionStatus

if TYPE_CHECKING:
    from ...semantic.symbol_table import SymbolTable
    from ...vnodes.identifier_vnode import IdentifierNameVNode
    from ...walk.context import Context


class SymbolResolver:
    """Looks an identifier up against scopes or packages. It reads the symbol table and never changes it."""

    def __init__(
        self,
        qualifier_fn: Callable[[object], str | None] | None = None,
    ) -> None:
        self._qualifier_fn = qualifier_fn if qualifier_fn is not None else scoped_name_package_qualifier

    def resolve(
        self,
        name: str,
        vnode: IdentifierNameVNode,
        ctx: Context,
        symbol_table: SymbolTable,
    ) -> Resolution:
        """Return how `name` resolves from the current scope.

        A package-qualified name that this file cannot look into, a name an import could
        supply from a package no analysed file declares, or the first segment of a hierarchical path with no
        declaration here (a generate-block label, say), is UNRESOLVABLE_HERE: it is neither
        declared nor undeclared as far as this file can tell. Any other miss is unresolved, and
        `default_nettype` decides which kind.
        """
        package_qualifier = self._qualifier_fn(vnode.raw)
        if package_qualifier is not None:
            symbol = ctx.scope().lookup_package_member(package_qualifier, name)
            if symbol is None:
                return Resolution(ResolutionStatus.UNRESOLVABLE_HERE)
            return Resolution(ResolutionStatus.RESOLVED, symbol)

        symbol = symbol_table.lookup_from_scope(name, ctx.scope())
        if symbol is not None:
            return Resolution(ResolutionStatus.RESOLVED, symbol)

        if ctx.scope().may_come_from_unseen_package(name) or is_hierarchical_path_base(vnode.raw):
            return Resolution(ResolutionStatus.UNRESOLVABLE_HERE)

        if symbol_table.current_file_uses_default_nettype_none():
            return Resolution(ResolutionStatus.UNRESOLVED_UNDECLARED)
        return Resolution(ResolutionStatus.UNRESOLVED_IMPLICIT_NET)
