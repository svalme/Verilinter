"""Keep aggregate fields and generate-loop locals out of enclosing namespaces."""
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
        if str(vnode.raw.genvar).strip():
            # The inline genvar name is a token, not a DeclaratorSyntax.
            symbol = Symbol(name=vnode.raw.identifier.value, kind="genvar")
            symbol.add_declaration(vnode.location)
            scope.define(symbol)
        return ctx.push(vnode).with_scope(scope)

    def on_exit(self, ctx, vnode, symbol_table):
        symbol_table.pop_scope()
