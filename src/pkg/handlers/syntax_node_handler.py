import pyslang as sl

from ..ast.context import Context
from ..ast.symbol_table import SymbolTable
from .base_handler import BaseHandler
from ..vnodes.base_vnode import BaseVNode
from ..vnodes.syntax_vnode import SyntaxVNode
from ..vnodes.token_vnode import TokenVNode

from ..ast.dispatch import dispatch
from ..vnodes.vnode_factory import vnode_factory

@dispatch.register(sl.SyntaxNode)
class SyntaxNodeHandler(BaseHandler[SyntaxVNode]):

    def matches(self, vnode) -> bool:
        return isinstance(vnode.raw, sl.SyntaxNode)

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        return ctx.push(vnode)

    def children(self, vnode: SyntaxVNode) -> list[BaseVNode]:
        out = []
        for child in vnode.children:
            out.append(vnode_factory.create(child, vnode.tree))
        return out
    
    def __str__(self) -> str:
        return "SyntaxNodeHandler"
