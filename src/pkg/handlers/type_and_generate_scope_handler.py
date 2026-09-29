"""Keep aggregate fields and generate-loop locals out of enclosing namespaces."""
from ..parser.syntax import loop_generate_genvar_name
from ..parser.types import StructUnionTypeNode, LoopGenerateNode
from ..semantic.symbol import Symbol
from ..walk.dispatch import dispatch
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(StructUnionTypeNode)
class StructUnionTypeHandler(SyntaxNodeHandler):
    def update_context(self, ctx, vnode, symbol_table):
        scope = symbol_table.new_scope(kind="aggregate", location=vnode.location)
        return ctx.push(vnode).with_scope(scope)

    def on_exit(self, ctx, vnode, symbol_table):
        symbol_table.pop_scope()


@dispatch.register(LoopGenerateNode)
class LoopGenerateHandler(SyntaxNodeHandler):
    def update_context(self, ctx, vnode, symbol_table):
        scope = symbol_table.new_scope(kind="generate_for", location=vnode.location)
        genvar_name = loop_generate_genvar_name(vnode.raw)
        if genvar_name:
            symbol = Symbol(name=genvar_name, kind="genvar")
            symbol.add_declaration(vnode.location)
            scope.define(symbol)
        return ctx.push(vnode).with_scope(scope)

    def on_exit(self, ctx, vnode, symbol_table):
        symbol_table.pop_scope()
