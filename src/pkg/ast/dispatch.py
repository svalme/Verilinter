# src/pkg/ast/dispatch.py

class Dispatch:
    def __init__(self):
        self._default = None
        self._registry = {}

    def set_default(self, handler):
        self._default = handler

    def register(self, raw_cls):
        def decorator(handler):
            self._registry[raw_cls] = handler()
            return handler
        return decorator

    def get(self, vnode):
        for cls in type(vnode.raw).__mro__:
            if cls in self._registry:
                return self._registry[cls]
        return self._default

dispatch = Dispatch()