from .dispatch import Dispatch
from .context import Context

from ..vnode.base_vnode import BaseVNode
from ..ast.symbol_table import SymbolTable

class Walker:
    def __init__(self, dispatch: Dispatch):
        self._dispatch = dispatch
        self._results = []

    def walk(self, vnode: BaseVNode, ctx: Context, symbol_table: SymbolTable):
        handler = self._dispatch.get(vnode)

        ctx = handler.update_context(ctx, vnode, symbol_table) # update context if necessary

        self._results.append((vnode, ctx)) # add observation

        for child in handler.children(vnode):
            self.walk(child, ctx, symbol_table)
