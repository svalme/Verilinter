from enum import Enum, auto
from ..vnode.base_vnode import BaseVNode
from .symbol_table import Scope

"""
class Scope:
    def __init__(self, name: str, kind: str, owner_vnode: BaseVNode):
        self.name = name
        self.kind = kind
        self.owner = owner_vnode
        self.symbols = {}
"""

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

    def __init__(self, stack=[], flags=set(), scopes=[]):
        self.stack: list[BaseVNode] = stack
        self.flags: set[ContextFlag] = flags
        self.scopes: list[Scope] = scopes

    def push(self, vnode: BaseVNode) -> Context:
        return Context(stack=self.stack + [vnode], flags=self.flags, scopes=self.scopes)

    def with_flag(self, flag: ContextFlag) -> Context:
        return Context(stack=self.stack, flags=self.flags | {flag}, scopes=self.scopes)

    def has(self, flag: ContextFlag) -> bool:
        return flag in self.flags

    def push_scope(self, new_scope: Scope) -> Context:
        return Context(stack=self.stack, flags=self.flags, scopes=self.scopes + [new_scope])
    
    def with_scope(self, scope):
        return Context(stack=self.stack, flags=self.flags, scopes=[scope])

    def scope(self) -> Scope | None:
        return self.scopes[-1] if self.scopes else None
    
    def __repr__(self):
        return f"stack: {self.stack} \nflags: {self.flags} \nscopes: {self.scopes}"
            