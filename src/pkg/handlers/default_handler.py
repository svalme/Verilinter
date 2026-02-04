# handlers/default_handler.py
from .base_handler import BaseHandler
from ..vnode.base_vnode import BaseVNode
from ..ast.context import Context
from ..ast.symbol_table import SymbolTable

class DefaultHandler(BaseHandler):
    
    def children(self, vnode: BaseVNode) -> list[BaseVNode]:
        return vnode.children if hasattr(vnode, 'children') else []
        #return []
    
    def update_context(self, ctx: Context, vnode: BaseVNode, symbol_table: SymbolTable) -> Context:
        return ctx.push(vnode)
    
    def __str__(self) -> str:
        return "DefaultHandler"