# vnode/vnode_factory.py
from typing import Type, Dict, TypeVar

from .token_vnode import TokenVNode
from .base_vnode import BaseVNode
from .syntax_vnode import SyntaxVNode
from ..parser.types import RawNode, SyntaxTree, Token

_VNodeT = TypeVar('_VNodeT', bound=BaseVNode)

class VNodeFactory:

    # registry: maps raw parser types --> vnode classes
    _node_map: Dict[Type, Type[BaseVNode]] = {}

    @classmethod
    def register(cls, raw_type: Type):
        def decorator(vnode_class: Type[_VNodeT]) -> Type[_VNodeT]:
            cls._node_map[raw_type] = vnode_class
            return vnode_class
        return decorator
    
    @classmethod
    def create(cls, raw: RawNode, tree: SyntaxTree) -> BaseVNode:
        # if a vnode is passed in, return it unchanged
        if isinstance(raw, BaseVNode):
            return raw

        for base in type(raw).__mro__:
            if base in cls._node_map:
                return cls._node_map[base](raw, tree)

        if isinstance(raw, Token):
            return TokenVNode(raw, tree)

        return SyntaxVNode(raw, tree)

vnode_factory = VNodeFactory()
