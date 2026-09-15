from __future__ import annotations

from typing import TYPE_CHECKING

from ...parser.syntax import scoped_name_package_qualifier
from ...semantic.symbol import Symbol

if TYPE_CHECKING:
    from ...semantic.symbol_table import SymbolTable
    from ...vnodes.identifier_vnode import IdentifierNameVNode
    from ...walk.context import Context


class SymbolResolver:
    """Resolves identifier names against scopes or packages, synthesizing implicit

    nets or variables when appropriate.
    """

    def resolve_or_create(
        self,
        name: str,
        vnode: IdentifierNameVNode,
        ctx: Context,
        symbol_table: SymbolTable,
    ) -> Symbol | None:
        """Resolve the symbol for the given identifier, or synthesize a new symbol

        in current scope if undeclared.

        Returns None if the identifier is explicitly package-qualified but the
        package or symbol is not found (avoiding false implicit-net creation).
        """
        package_qualifier = scoped_name_package_qualifier(vnode.raw)
        if package_qualifier is not None:
            package_scope = symbol_table.lookup_package(package_qualifier)
            symbol = package_scope.lookup(name) if package_scope is not None else None
            if symbol is None:
                # Either the package isn't declared in this file or this narrow
                # same-file lookup didn't find the name in it. Skip rather than
                # manufacture a false implicit net.
                return None
            return symbol

        symbol = symbol_table.lookup_from_scope(name, ctx.scope())
        if symbol is not None:
            return symbol

        # Synthesize implicit net or variable according to current file default_nettype
        if symbol_table.current_file_uses_default_nettype_none():
            symbol = Symbol(name=name, kind="variable")
        else:
            symbol = Symbol(name=name, kind="implicit_net")
            symbol.is_implicit = True

        ctx.scope().define(symbol)
        return symbol
