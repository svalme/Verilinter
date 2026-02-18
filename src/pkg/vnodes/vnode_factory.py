# vnode/vnode_factory.py
from typing import Type, Dict
import pyslang as sl

from .token_vnode import TokenVNode
from .base_vnode import BaseVNode
from .syntax_vnode import SyntaxVNode

class VNodeFactory:
    
    # registry: maps raw pyslang types --> vnode classes
    _node_map: Dict[Type, Type[BaseVNode]] = {}
    
    @classmethod
    def register(cls, raw_type: Type):
        def decorator(vnode_class: Type[BaseVNode]):
            cls._node_map[raw_type] = vnode_class
            return vnode_class
        return decorator
    
    @classmethod
    def create(cls, raw: sl.Token | sl.SyntaxNode, tree: sl.SyntaxTree) -> BaseVNode:
        # if a vnode is passed in, return it unchanged
        if isinstance(raw, BaseVNode):
            return raw

        for base in type(raw).__mro__:
            if base in cls._node_map:
                return cls._node_map[base](raw, tree)

        if isinstance(raw, sl.Token):
            return TokenVNode(raw, tree)

        return SyntaxVNode(raw, tree)

vnode_factory = VNodeFactory()