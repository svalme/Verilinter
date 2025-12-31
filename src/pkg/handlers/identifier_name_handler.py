import pyslang as sl
from ..ast.dispatch import dispatch
from ..ast.context import Context, ContextFlag
from ..ast.symbol_table import Symbol, SymbolTable, Scope
from ..vnode.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler

@dispatch.register(sl.IdentifierNameSyntax)
class IdentifierNameHandler(SyntaxNodeHandler):

    def update_context(self, ctx, vnode: SyntaxVNode, symbol_table: SymbolTable):
        name = vnode.raw.identifier.value
        symbol = symbol_table.lookup(name)

        if symbol:
            symbol.add_use(vnode.location, read=True)
        else:
            symbol = Symbol(name=name, kind="variable")
            symbol.set_scope(ctx.scope())
            symbol.add_use(vnode.location, read=True)
            ctx.scope().define(symbol)

        return ctx.push(vnode)

    def __str__(self) -> str:
        return "IdentifierNameHandler"