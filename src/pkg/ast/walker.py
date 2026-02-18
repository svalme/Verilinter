import pyslang as sl

from .dispatch import Dispatch
from .context import Context

from ..vnodes.register_vnodes import *
from ..vnodes.base_vnode import BaseVNode
from ..vnodes.vnode_factory import vnode_factory
from ..ast.symbol_table import SymbolTable

class Walker:
    def __init__(self, dispatch: Dispatch):
        self._dispatch = dispatch
        self._results = []

    def walk(self, raw_node: sl.SyntaxNode | sl.Token | BaseVNode, tree: sl.SyntaxTree, ctx: Context, symbol_table: SymbolTable):

        # if a vnode was passed in, use it directly; otherwise create one
        if isinstance(raw_node, BaseVNode):
            vnode = raw_node
            #print(f"VNode passed in directly: {vnode} (type: {type(vnode)})")
        else:
            vnode = vnode_factory.create(raw_node, tree)

        handler = self._dispatch.get(vnode)

        ctx = handler.update_context(ctx, vnode, symbol_table) 

        self._results.append((vnode, ctx)) # add observation

        for child_vnode in handler.children(vnode):
            self.walk(child_vnode, tree, ctx, symbol_table)
