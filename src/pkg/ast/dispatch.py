# src/pkg/ast/dispatch.py
from typing import TypeVar, cast
from ..vnodes.base_vnode import BaseVNode
from ..handlers.base_handler import BaseHandler
from ..handlers.default_handler import DefaultHandler

class Dispatch:
    def __init__(self):
        self._default: BaseHandler[BaseVNode] = DefaultHandler()  
        self._registry: dict = {}

    def register(self, raw_cls):
        def decorator(handler_cls):
            self._registry[raw_cls] = handler_cls()
            return handler_cls
        return decorator

    def get(self, vnode: BaseVNode) -> BaseHandler: 
        for cls in type(vnode.raw).__mro__:
            if cls in self._registry:
                return  self._registry[cls]
        return self._default
    
dispatch = Dispatch()