# src/pkg/ast/dispatch.py
from ..handlers.base_handler import BaseHandler
from ..handlers.default_handler import DefaultHandler

class Dispatch:
    def __init__(self):
        self._default: BaseHandler = DefaultHandler()  
        self._registry: dict = {}

    def register(self, raw_cls):
        def decorator(handler):
            self._registry[raw_cls] = handler()
            return handler
        return decorator

    def get(self, vnode) -> BaseHandler: 
        for cls in type(vnode.raw).__mro__:
            if cls in self._registry:
                return self._registry[cls]
        return self._default

dispatch = Dispatch()