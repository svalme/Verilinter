# src/pkg/walk/dispatch.py
from typing import Any, Callable

from ..handlers.base_handler import BaseHandler
from ..handlers.default_handler import DefaultHandler
from ..vnodes.base_vnode import BaseVNode


class Dispatch:
    def __init__(self) -> None:
        self._default: BaseHandler[BaseVNode] = DefaultHandler()
        self._registry: dict[type[Any], BaseHandler[BaseVNode]] = {}
        self._resolved: dict[type[Any], BaseHandler[BaseVNode]] = {}

    def register(self, raw_cls: type[Any]) -> Callable[[type[BaseHandler[BaseVNode]]], type[BaseHandler[BaseVNode]]]:
        def decorator(handler_cls: type[BaseHandler[BaseVNode]]) -> type[BaseHandler[BaseVNode]]:
            self._registry[raw_cls] = handler_cls()
            self._resolved.clear()
            return handler_cls

        return decorator

    def get(self, vnode: BaseVNode) -> BaseHandler[BaseVNode]:
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
