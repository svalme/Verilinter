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

    def __init__(self, flags: set[ContextFlag] | None = None, scope: Scope | None = None,
                 *, _parent: "Context | None" = None, _vnode: BaseVNode | None = None):
        self._parent = _parent
        self._vnode = _vnode
        self.flags = flags if flags is not None else set()
        self._scope = scope

    @property
    def stack(self) -> list[BaseVNode]:
        """Ancestor chain from root to current node, rebuilt on demand from parent pointers."""
        nodes: list[BaseVNode] = []
        node: "Context | None" = self
        while node is not None and node._vnode is not None:
            nodes.append(node._vnode)
            node = node._parent
        nodes.reverse()
        return nodes

    def push(self, vnode: BaseVNode) -> "Context":
        return Context(flags=self.flags, scope=self._scope, _parent=self, _vnode=vnode)

    def with_flag(self, flag: ContextFlag) -> "Context":
        return Context(flags=self.flags | {flag}, scope=self._scope, _parent=self._parent, _vnode=self._vnode)

    def has(self, flag: ContextFlag) -> bool:
        return flag in self.flags

    def with_scope(self, scope: Scope) -> "Context":
        return Context(flags=self.flags, scope=scope, _parent=self._parent, _vnode=self._vnode)

    def scope(self) -> Scope:
        if self._scope is None:
            raise RuntimeError("Context has no scope")
        return self._scope

    def __repr__(self) -> str:
        return f"stack: {self.stack} \nflags: {self.flags} \nscope: {self._scope}"
