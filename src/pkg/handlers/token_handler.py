from ..walk.context import Context
from ..semantic.symbol_table import SymbolTable
from .base_handler import BaseHandler
from ..vnodes.base_vnode import BaseVNode
from ..vnodes.token_vnode import TokenVNode

from ..walk.dispatch import dispatch
from ..parser.types import Token

@dispatch.register(Token)
class TokenHandler(BaseHandler[TokenVNode]):

    def update_context(self, ctx: Context, vnode: TokenVNode, symbol_table: SymbolTable) -> Context:
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "TokenHandler"

    
