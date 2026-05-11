from ..vnodes.base_vnode import BaseVNode
from ..ast.context import Context
from ..ast.symbol_table import SymbolTable
from typing import TypeVar, Generic

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