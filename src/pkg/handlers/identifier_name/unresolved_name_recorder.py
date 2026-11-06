from __future__ import annotations

from typing import TYPE_CHECKING

from ...semantic.resolution import Resolution, ResolutionStatus, UnresolvedReference
from ...semantic.scope import enclosing_name_owning_scope
from ...semantic.symbol import Symbol
from ...semantic.symbol_kind import SymbolKind

if TYPE_CHECKING:
    from ...semantic.symbol_table import SymbolTable
    from ...vnodes.identifier_vnode import IdentifierNameVNode
    from ...walk.context import Context


class UnresolvedNameRecorder:
    """Records a name that has no declaration and provides the placeholder that collects its uses.

    The placeholder lives in the enclosing module, package or subroutine scope, so a name used in several
    generate blocks is one placeholder and one reference. Rules read `symbol_table.unresolved_references`
    for the findings, and read the placeholder symbol only as a use-tracking symbol.
    """

    def record(
        self,
        name: str,
        resolution: Resolution,
        vnode: IdentifierNameVNode,
        ctx: Context,
        symbol_table: SymbolTable,
    ) -> Symbol | None:
        """Return the placeholder to attach the use to, or None when the name should not be tracked."""
        status = resolution.status
        if status is ResolutionStatus.RESOLVED:
            return resolution.symbol
        if status is ResolutionStatus.UNRESOLVABLE_HERE:
            symbol_table.unresolved_references.append(UnresolvedReference(name, status, vnode.location))
            return None

        kind = (
            SymbolKind.IMPLICIT_NET
            if status is ResolutionStatus.UNRESOLVED_IMPLICIT_NET
            else SymbolKind.VARIABLE
        )
        placeholder = Symbol(name=name, kind=kind)
        enclosing_name_owning_scope(ctx.scope()).define(placeholder)
        symbol_table.unresolved_references.append(UnresolvedReference(name, status, vnode.location, placeholder))
        return placeholder
