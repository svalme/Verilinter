from ..walk.dispatch import dispatch
from ..walk.context import Context
from ..parser.syntax import is_package_declaration_node, module_declaration_name
from ..semantic.symbol_table import SymbolTable
from ..vnodes.syntax_vnode import SyntaxVNode
from ..parser.types import ModuleDeclarationNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(ModuleDeclarationNode)
class ModuleDeclarationHandler(SyntaxNodeHandler):

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        name = module_declaration_name(vnode.raw) or "<anonymous>"
        # pyslang represents `package`/`module`/`interface`/`program` declarations
        # with the same wrapper class, distinguishable only by `.kind` -- a
        # package must get its own "package" scope registered via
        # register_package, not register_module, or it pollutes
        # UNDEFINED_MODULE/DUPLICATE_MODULE's module registry.
        if is_package_declaration_node(vnode.raw):
            package_scope = symbol_table.new_scope(
                kind="package",
                name=name,
                parent=symbol_table.global_scope,
                location=vnode.location,
            )
            symbol_table.register_package(name, package_scope)
            return ctx.push(vnode).with_scope(package_scope)

        module_scope = symbol_table.new_scope(
            kind="module",
            name=name,
            parent=symbol_table.global_scope,
            location=vnode.location,
        )
        symbol_table.register_module(name, module_scope)
        return ctx.push(vnode).with_scope(module_scope)

    def on_exit(self, _ctx: Context, _vnode: SyntaxVNode, symbol_table: SymbolTable) -> None:
        symbol_table.pop_scope()

    def __str__(self) -> str:
        return "ModuleDeclarationHandler"
