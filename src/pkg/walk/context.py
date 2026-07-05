from enum import Enum, auto
from ..vnodes.base_vnode import BaseVNode
from ..semantic.scope import Scope

class ContextFlag(Enum):

    # --- Timing / sensitivity ---
    HAS_EVENT_CONTROL = auto()
    POSEDGE = auto()
    NEGEDGE = auto()

    # --- Semantic classification ---
    ALWAYS = auto()        # always @(posedge/negedge ...)
    ALWAYS_COMB = auto()      # always_comb / always @*
    ALWAYS_LATCH = auto()

    # --- Statement-level ---
    IN_EXPRESSION = auto()
    IN_ASSIGNMENT = auto()
    BLOCKING_ASSIGN = auto()
    NONBLOCKING_ASSIGN = auto()

    CASE_GENERATE = auto()
    DEFAULT = auto()


class Context:

    def __init__(self, stack: list[BaseVNode] | None = None, flags: set[ContextFlag] | None = None, scope: Scope | None = None):
        self.stack = stack if stack is not None else []
        self.flags = flags if flags is not None else set()
        self._scope = scope

    def push(self, vnode: BaseVNode) -> "Context":
        return Context(stack=self.stack + [vnode], flags=self.flags, scope=self._scope)

    def with_flag(self, flag: ContextFlag) -> "Context":
        return Context(stack=self.stack, flags=self.flags | {flag}, scope=self._scope)

    def has(self, flag: ContextFlag) -> bool:
        return flag in self.flags

    def with_scope(self, scope: Scope) -> "Context":
        return Context(stack=self.stack, flags=self.flags, scope=scope)

    def scope(self) -> Scope:
        if self._scope is None:
            raise RuntimeError("Context has no scope")
        return self._scope

    def __repr__(self) -> str:
        return f"stack: {self.stack} \nflags: {self.flags} \nscope: {self._scope}"
