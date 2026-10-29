from __future__ import annotations

from ..parser.syntax import member_selector_base_name
from ..parser.types import IDENTIFIER_NAME_NODE_TYPES
from ..semantic.symbol_table import SymbolTable
from ..vnodes.base_vnode import BaseVNode
from ..vnodes.identifier_vnode import IdentifierNameVNode
from ..vnodes.vnode_factory import vnode_factory
from ..walk.context import Context
from ..walk.dispatch import dispatch
from .base_handler import BaseHandler
from .identifier_name import (
    DEFAULT_STRUCTURAL_NAME_PREDICATES,
    StructuralReferenceFilter,
    SymbolResolver,
    UseEventContextExtractor,
)

# Re-exported for backward compatibility with existing tests/documentation
_STRUCTURAL_NAME_PREDICATES = DEFAULT_STRUCTURAL_NAME_PREDICATES


def _is_structural_name_reference(raw: object) -> bool:
    return any(predicate(raw) for predicate in _STRUCTURAL_NAME_PREDICATES)


class IdentifierNameHandler(BaseHandler[IdentifierNameVNode]):
    """Orchestrates identifier reference handling: filtering structural names,

    resolving or synthesizing symbols, and extracting use-event context.
    """

    def __init__(
        self,
        filter: StructuralReferenceFilter | None = None,
        resolver: SymbolResolver | None = None,
        extractor: UseEventContextExtractor | None = None,
    ) -> None:
        self.filter = filter if filter is not None else StructuralReferenceFilter()
        self.resolver = resolver if resolver is not None else SymbolResolver()
        self.extractor = extractor if extractor is not None else UseEventContextExtractor()

    def update_context(
        self,
        ctx: Context,
        vnode: IdentifierNameVNode,
        symbol_table: SymbolTable,
    ) -> Context:
        name = vnode.identifier_name
        if not name:
            return ctx.push(vnode)
        if self.filter.is_structural_reference(vnode.raw):
            self._record_interface_member_use(name, ctx, vnode, symbol_table)
            return ctx.push(vnode)

        symbol = self.resolver.resolve_or_create(name, vnode, ctx, symbol_table)
        if symbol is None:
            return ctx.push(vnode)

        event_context = self.extractor.extract(vnode, ctx, symbol_table)
        symbol.add_use(vnode.location, **event_context.to_use_kwargs())

        return ctx.push(vnode)

    def _record_interface_member_use(
        self,
        member: str,
        ctx: Context,
        vnode: IdentifierNameVNode,
        symbol_table: SymbolTable,
    ) -> None:
        base_name = member_selector_base_name(vnode.raw)
        if base_name is None:
            return
        base = symbol_table.lookup_from_scope(base_name, ctx.scope())
        if base is None or base.interface_type_name is None:
            return
        event_context = self.extractor.extract(vnode, ctx, symbol_table)
        symbol_table.record_interface_member_use(
            base.interface_type_name, member, vnode.location, event_context.to_use_kwargs()
        )

    def children(self, vnode: IdentifierNameVNode) -> list[BaseVNode]:
        return [vnode_factory.create(child, vnode.tree) for child in vnode.raw_children]

    def __str__(self) -> str:
        return "IdentifierNameHandler"


for _raw_type in IDENTIFIER_NAME_NODE_TYPES:
    dispatch.register(_raw_type)(IdentifierNameHandler)
