from ..walk.dispatch import dispatch
from ..walk.context import Context
from ..parser.syntax import (
    declarator_bit_width,
    declarator_has_initializer,
    declarator_is_parameter,
    declarator_is_port,
    declarator_is_signed,
    declarator_name,
    declarator_port_direction,
)
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
        kind = "parameter" if declarator_is_parameter(ctx) else "variable"
        symbol = Symbol(name=name, kind=kind)
        symbol.is_port = declarator_is_port(ctx)
        if symbol.is_port:
            symbol.port_direction = declarator_port_direction(ctx)
        symbol.bit_width = declarator_bit_width(ctx)
        symbol.is_signed = declarator_is_signed(ctx)
        symbol.add_declaration(vnode.location)
        if declarator_has_initializer(vnode.raw):
            symbol.add_use(vnode.location, write=True)
        ctx.scope().define(symbol)
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "DeclaratorHandler"
