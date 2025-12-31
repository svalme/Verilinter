from ..vnode.base_vnode import BaseVNode
from ..ast.context import Context

class BaseHandler:

    def children(self, vnode: BaseVNode) -> list[BaseVNode]:
        pass

    def update_context(self, ctx: Context, vnode: BaseVNode, symbol_table=None) -> Context:
        pass