import pyslang as sl
from ..walk.dispatch import dispatch
from ..walk.context import Context, ContextFlag
from ..semantic.symbol_table import SymbolTable
from ..vnodes.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(sl.ModuleDeclarationSyntax)
class ModuleDeclarationHandler(SyntaxNodeHandler):

    def update_context(self, ctx, vnode, symbol_table: SymbolTable):
        name = vnode.raw.header.name.value
        module_scope = symbol_table.new_scope(
            kind="module",
            name=name,
            parent=symbol_table.global_scope,
            location=vnode.location,
        )
        symbol_table.register_module(name, module_scope)
        return ctx.push(vnode).with_scope(module_scope)

    def on_exit(self, _ctx, _vnode, symbol_table: SymbolTable) -> None:
        symbol_table.pop_scope()

    def __str__(self) -> str:
        return "ModuleDeclarationHandler"
