import pyslang as sl

from .base_handler import BaseHandler
from ..vnodes.base_vnode import BaseVNode
from ..vnodes.identifier_vnode import IdentifierNameVNode
from ..vnodes.vnode_factory import vnode_factory
from ..walk.dispatch import dispatch
from ..semantic.symbol import Symbol
from ..semantic.symbol_table import SymbolTable
from ..walk.context import Context

@dispatch.register(sl.IdentifierNameSyntax)
class IdentifierNameHandler(BaseHandler[IdentifierNameVNode]):

    def update_context(self, ctx: Context, vnode: IdentifierNameVNode, symbol_table: SymbolTable) -> Context:
        name = vnode.identifier_name
        if not name:
            return ctx.push(vnode)
        symbol = symbol_table.lookup_from_scope(name, ctx.scope())

        if symbol:
            symbol.add_use(vnode.location, read=True)
        else:
            symbol = Symbol(name=name, kind="variable")
            symbol.is_implicit = True
            symbol.add_use(vnode.location, read=True)
            ctx.scope().define(symbol)

        return ctx.push(vnode)

    def children(self, vnode: IdentifierNameVNode) -> list[BaseVNode]:
        return [vnode_factory.create(child, vnode.tree) for child in vnode.raw_children]

    def __str__(self) -> str:
        return "IdentifierNameHandler"
