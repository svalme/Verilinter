import pyslang as sl

from ..ast.context import Context
from ..ast.symbol_table import SymbolTable
from .base_handler import BaseHandler
from ..vnodes.base_vnode import BaseVNode
from ..vnodes.token_vnode import TokenVNode

from ..ast.dispatch import dispatch

@dispatch.register(sl.Token)
class TokenHandler(BaseHandler[TokenVNode]):

    def update_context(self, ctx: Context, vnode: TokenVNode, symbol_table: SymbolTable) -> Context:
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "TokenHandler"

    