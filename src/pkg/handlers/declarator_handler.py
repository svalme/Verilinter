import pyslang as sl
from ..ast.dispatch import dispatch
from ..ast.context import Context
from ..ast.symbol_table import Symbol, SymbolTable
from ..vnode.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(sl.DeclaratorSyntax)
class DeclaratorHandler(SyntaxNodeHandler):

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        name = vnode.raw.name.value
        symbol = Symbol(name=name, kind="variable")
        symbol.add_declaration(vnode.location)
        symbol.set_scope(ctx.scope())

        scope = ctx.scope()
 
        if scope:
            scope.define(symbol)
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "DeclaratorHandler"