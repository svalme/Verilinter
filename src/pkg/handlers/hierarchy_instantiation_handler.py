from ..walk.dispatch import dispatch
from ..walk.context import Context
from ..semantic.symbol import Symbol
from ..semantic.symbol_table import SymbolTable
from ..parser.syntax import hierarchical_instance_name, instantiation_type_name
from ..parser.types import HierarchicalInstanceNode, HierarchyInstantiationNode
from ..vnodes.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(HierarchyInstantiationNode)
class HierarchyInstantiationHandler(SyntaxNodeHandler):

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        type_name = instantiation_type_name(vnode.raw)
        if type_name:
            symbol_table.register_module_reference(type_name, vnode.location)

        for item in vnode.raw.instances:
            if isinstance(item, HierarchicalInstanceNode):
                inst_name = hierarchical_instance_name(item)
                if inst_name:
                    sym = Symbol(name=inst_name, kind="instance")
                    sym.add_declaration(vnode.location)
                    ctx.scope().define(sym)

        return ctx.push(vnode)

    def __str__(self) -> str:
        return "HierarchyInstantiationHandler"
