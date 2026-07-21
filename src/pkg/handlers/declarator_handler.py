from ..walk.dispatch import dispatch
from ..walk.context import Context
from ..parser.syntax import declarator_has_initializer, declarator_is_port, declarator_name
from ..semantic.symbol import Symbol
from ..semantic.symbol_table import SymbolTable
from ..parser.types import DeclaratorNode
from ..vnodes.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(DeclaratorNode)
class DeclaratorHandler(SyntaxNodeHandler):
    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        name = declarator_name(vnode.raw)
        if not name:
            return ctx.push(vnode)
        symbol = Symbol(name=name, kind="variable")
        symbol.is_port = declarator_is_port(ctx)
        symbol.add_declaration(vnode.location)
        if declarator_has_initializer(vnode.raw):
            symbol.add_use(vnode.location, write=True)
        ctx.scope().define(symbol)
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "DeclaratorHandler"
