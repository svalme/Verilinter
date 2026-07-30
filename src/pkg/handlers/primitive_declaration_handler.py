from ..walk.dispatch import dispatch
from ..walk.context import Context
from ..parser.syntax import primitive_declaration_name
from ..semantic.symbol_table import SymbolTable
from ..vnodes.syntax_vnode import SyntaxVNode
from ..parser.types import PrimitiveDeclarationNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(PrimitiveDeclarationNode)
class PrimitiveDeclarationHandler(SyntaxNodeHandler):
    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        name = primitive_declaration_name(vnode.raw)
        if name:
            symbol_table.register_primitive(name)
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "PrimitiveDeclarationHandler"
