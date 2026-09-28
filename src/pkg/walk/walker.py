from typing import Any, Callable

from .dispatch import Dispatch
from .context import Context

from ..vnodes.register_vnodes import *
from ..vnodes.base_vnode import BaseVNode
from ..vnodes.vnode_factory import vnode_factory as default_vnode_factory
from ..semantic.symbol_table import SymbolTable
from ..parser.types import RawNode, SyntaxTree


class Walker:
    def __init__(self, dispatch: Dispatch, vnode_factory: Any = None) -> None:
        self._dispatch = dispatch
        self._vnode_factory = vnode_factory if vnode_factory is not None else default_vnode_factory
        self._results: list[tuple[BaseVNode, Context]] = []

    @property
    def results(self) -> list[tuple[BaseVNode, Context]]:
        return self._results

    def walk(
        self,
        raw_node: RawNode | BaseVNode,
        tree: SyntaxTree,
        ctx: Context,
        symbol_table: SymbolTable,
        on_node: Callable[[BaseVNode, Context], None] | None = None,
    ) -> None:
        visited: set[int] = set()

        def _walk(node: RawNode | BaseVNode, ctx: Context, depth: int = 0) -> None:
            if depth >= 256:
                return
            raw = getattr(node, "raw", node)
            nid = id(raw)
            if nid in visited:
                return
            visited.add(nid)
            try:
                vnode = node if isinstance(node, BaseVNode) else self._vnode_factory.create(node, tree)
                handler = self._dispatch.get(vnode)
                ctx = handler.update_context(ctx, vnode, symbol_table)
                if on_node is not None:
                    on_node(vnode, ctx)
                else:
                    self._results.append((vnode, ctx))
                for child in handler.children(vnode):
                    _walk(child, ctx, depth + 1)
                handler.on_exit(ctx, vnode, symbol_table)
            finally:
                visited.remove(nid)

        _walk(raw_node, ctx)
