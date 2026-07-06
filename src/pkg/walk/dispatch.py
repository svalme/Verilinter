# src/pkg/walk/dispatch.py
from typing import TypeVar, cast
from ..vnodes.base_vnode import BaseVNode
from ..handlers.base_handler import BaseHandler
from ..handlers.default_handler import DefaultHandler

class Dispatch:
    def __init__(self):
        self._default: BaseHandler[BaseVNode] = DefaultHandler()
        self._registry: dict = {}
        self._resolved: dict = {}

    def register(self, raw_cls):
        def decorator(handler_cls):
            self._registry[raw_cls] = handler_cls()
            self._resolved.clear()
            return handler_cls
        return decorator

    def get(self, vnode: BaseVNode) -> BaseHandler:
        raw_cls = type(vnode.raw)
        handler = self._resolved.get(raw_cls)
        if handler is not None:
            return handler

        for cls in raw_cls.__mro__:
            if cls in self._registry:
                handler = self._registry[cls]
                break
        else:
            handler = self._default

        self._resolved[raw_cls] = handler
        return handler

dispatch = Dispatch()
