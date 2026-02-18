from ..vnodes.base_vnode import BaseVNode
from ..ast.context import Context
from ..ast.symbol_table import SymbolTable
from abc import ABC
from typing import TypeVar, Generic

VNodeType = TypeVar("VNodeType", bound=BaseVNode)

class BaseHandler(ABC, Generic[VNodeType]):

    def children(self, vnode: VNodeType) -> list[BaseVNode]:
        return []


    def update_context(self, ctx: Context, vnode: VNodeType, symbol_table: SymbolTable) -> Context:
        return ctx
        
    def __str__(self) -> str:
        return "BaseHandler"