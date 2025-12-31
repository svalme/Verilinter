import pyslang as sl

from ..ast.context import Context
from .base_handler import BaseHandler
from ..vnode.base_vnode import BaseVNode
from ..vnode.token_vnode import TokenVNode

from ..ast.dispatch import dispatch

@dispatch.register(sl.Token)
class TokenHandler(BaseHandler):

    def matches(self, vnode) -> bool:
        return isinstance(vnode.raw, sl.Token)

    def update_context(self, ctx: Context, vnode: TokenVNode, symbol_table=None) -> Context:
        return ctx.push(vnode)

    def children(self, vnode: TokenVNode) -> list[BaseVNode]:
        return []  
    
    def __str__(self) -> str:
        return "TokenHandler"

    