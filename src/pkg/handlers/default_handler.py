from .base_handler import BaseHandler
from ..vnodes.base_vnode import BaseVNode
from ..walk.context import Context
from ..semantic.symbol_table import SymbolTable
from ..vnodes.vnode_factory import vnode_factory

class DefaultHandler(BaseHandler):

    def children(self, vnode: BaseVNode) -> list[BaseVNode]:
        return [vnode_factory.create(child, vnode.tree) for child in vnode.raw_children]

    def update_context(self, ctx: Context, vnode: BaseVNode, symbol_table: SymbolTable) -> Context:
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "DefaultHandler"