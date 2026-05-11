import pyslang as sl

from ..ast.dispatch import dispatch
from ..ast.context import Context
from ..ast.symbol_table import Symbol, SymbolTable
from ..vnodes.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(sl.HierarchyInstantiationSyntax)
class HierarchyInstantiationHandler(SyntaxNodeHandler):

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        for item in vnode.raw.instances:
            if isinstance(item, sl.HierarchicalInstanceSyntax):
                inst_name = item.decl.name.value
                if inst_name:
                    sym = Symbol(name=inst_name, kind="instance")
                    sym.add_declaration(vnode.location)
                    ctx.scope().define(sym)

        return ctx.push(vnode)

    def __str__(self) -> str:
        return "HierarchyInstantiationHandler"
