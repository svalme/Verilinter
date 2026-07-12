from ..walk.dispatch import dispatch
from ..walk.context import Context, ContextFlag
from ..parser.syntax import module_declaration_name
from ..semantic.symbol_table import SymbolTable
from ..vnodes.syntax_vnode import SyntaxVNode
from ..parser.types import ModuleDeclarationNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(ModuleDeclarationNode)
class ModuleDeclarationHandler(SyntaxNodeHandler):

    def update_context(self, ctx, vnode, symbol_table: SymbolTable):
        name = module_declaration_name(vnode.raw) or "<anonymous>"
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
