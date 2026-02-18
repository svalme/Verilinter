import pyslang as sl
from typing import cast

from .base_handler import BaseHandler
from ..vnodes.identifier_vnode import IdentifierNameVNode
from ..ast.dispatch import dispatch
from ..ast.symbol_table import Symbol, SymbolTable, Scope
from ..ast.context import Context
from ..vnodes.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler

@dispatch.register(sl.IdentifierNameSyntax)
class IdentifierNameHandler(BaseHandler[IdentifierNameVNode]):

    def update_context(self, ctx: Context, vnode: IdentifierNameVNode, symbol_table: SymbolTable) -> Context:

        # for runtime safety: ensure vnode has identifier data before access
        if isinstance(vnode, IdentifierNameVNode):
            name = vnode.identifier_name
        else:
            # try to extract identifier from the raw syntax if available
            raw = getattr(vnode, 'raw', None)
            if raw is not None and hasattr(raw, 'identifier') and raw.identifier is not None:
                name = getattr(raw.identifier, 'value', '')
            else:
                # nothing to do for non-identifier nodes; push and continue
                return ctx.push(vnode)
        
        symbol = symbol_table.lookup(name)

        if symbol:
            symbol.add_use(vnode.location, read=True)
        else:
            symbol = Symbol(name=name, kind="variable")
            symbol.is_implicit = True 
            symbol.set_scope(ctx.scope())
            symbol.add_use(vnode.location, read=True)
            ctx.scope().define(symbol)

        return ctx.push(vnode)

    def children(self, vnode: IdentifierNameVNode) -> list:
        return getattr(vnode, 'children', [])

    def __str__(self) -> str:
        return "IdentifierNameHandler"