import pyslang as sl
from ..ast.dispatch import dispatch
from ..ast.context import Context, ContextFlag
from ..ast.symbol_table import Symbol, SymbolTable
from ..vnode.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler



@dispatch.register(sl.ModuleDeclarationSyntax)
class ModuleDeclarationHandler(SyntaxNodeHandler):

    def update_context(self, ctx, vnode, symbol_table: SymbolTable):
        name = vnode.raw.header.name.value

        module_scope = symbol_table.new_scope(
            kind="module",
            name=name,
            parent=symbol_table.global_scope,
        )

        return ctx.push(vnode).with_scope(module_scope)

    def __str__(self) -> str:
        return "ModuleDeclarationHandler"