from typing import Generic, TypeVar

from ..semantic.symbol_table import SymbolTable
from ..vnodes.base_vnode import BaseVNode
from ..walk.context import Context

VNodeType = TypeVar("VNodeType", bound=BaseVNode)


class BaseHandler(Generic[VNodeType]):
    def children(self, _vnode: VNodeType) -> list[BaseVNode]:
        return []

    def update_context(self, ctx: Context, _vnode: VNodeType, _symbol_table: SymbolTable) -> Context:
        return ctx

    def on_exit(self, _ctx: Context, _vnode: VNodeType, _symbol_table: SymbolTable) -> None:
        pass

    def __str__(self) -> str:
        return "BaseHandler"
