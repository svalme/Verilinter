import pyslang as sl

from ..ast.context import Context
from ..ast.symbol_table import SymbolTable
from .base_handler import BaseHandler
from ..vnode.base_vnode import BaseVNode
from ..vnode.syntax_vnode import SyntaxVNode
from ..vnode.token_vnode import TokenVNode

from ..ast.dispatch import dispatch

@dispatch.register(sl.SyntaxNode)
class SyntaxNodeHandler(BaseHandler[SyntaxVNode]):

    def matches(self, vnode) -> bool:
        return isinstance(vnode.raw, sl.SyntaxNode)

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        return ctx.push(vnode)

    def children(self, vnode: SyntaxVNode) -> list[BaseVNode]:
        out = []
        for child in vnode.children:
            if isinstance(child, sl.Token):
                out.append(TokenVNode(child, vnode.tree))
            else:
                out.append(SyntaxVNode(child, vnode.tree))
        return out
    
    def __str__(self) -> str:
        return "SyntaxNodeHandler"
