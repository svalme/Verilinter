from enum import Enum, auto
from ..vnodes.base_vnode import BaseVNode
from .symbol_table import Scope

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

    def __init__(self, stack: list[BaseVNode] | None = None, flags: set[ContextFlag] | None = None, scopes: list[Scope] | None = None):
        self.stack = stack if stack is not None else [] 
        self.flags = flags if flags is not None else set()
        self.scopes = scopes if scopes is not None else []

    def push(self, vnode: BaseVNode) -> Context:
        return Context(stack=self.stack + [vnode], flags=self.flags, scopes=self.scopes)

    def with_flag(self, flag: ContextFlag) -> Context:
        return Context(stack=self.stack, flags=self.flags | {flag}, scopes=self.scopes)

    def has(self, flag: ContextFlag) -> bool:
        return flag in self.flags

    def push_scope(self, new_scope: Scope) -> Context:
        return Context(stack=self.stack, flags=self.flags, scopes=self.scopes + [new_scope])
    
    def with_scope(self, scope: Scope) -> Context:
        return Context(stack=self.stack, flags=self.flags, scopes=[scope])

    def scope(self) -> Scope:
        if not self.scopes: 
            raise RuntimeError("Context has no scope")  
        return self.scopes[-1]
    
    def __repr__(self) -> str:
        return f"stack: {self.stack} \nflags: {self.flags} \nscopes: {self.scopes}"
            