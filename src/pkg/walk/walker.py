from typing import Callable

from .dispatch import Dispatch
from .context import Context

from ..vnodes.register_vnodes import *
from ..vnodes.base_vnode import BaseVNode
from ..vnodes.vnode_factory import vnode_factory
from ..semantic.symbol_table import SymbolTable
from ..parser.types import RawNode, SyntaxTree


class Walker:
    def __init__(self, dispatch: Dispatch):
        self._dispatch = dispatch
        self._results: list = []

    @property
    def results(self) -> list:
        return self._results

    def walk(self, raw_node: RawNode | BaseVNode, tree: SyntaxTree, ctx: Context, symbol_table: SymbolTable,
              on_node: Callable[[BaseVNode, Context], None] | None = None):
        def _walk(node: RawNode | BaseVNode, ctx: Context):
            vnode = node if isinstance(node, BaseVNode) else vnode_factory.create(node, tree)
            handler = self._dispatch.get(vnode)
            ctx = handler.update_context(ctx, vnode, symbol_table)
            if on_node is not None:
                on_node(vnode, ctx)
            else:
                self._results.append((vnode, ctx))
            for child in handler.children(vnode):
                _walk(child, ctx)
            handler.on_exit(ctx, vnode, symbol_table)

        _walk(raw_node, ctx)
