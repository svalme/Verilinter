from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable
from ..vnodes.base_vnode import BaseVNode
from ..semantic.scope import Scope


@dataclass(frozen=True)
class ModuleFrame:
    """Strongly typed contextual data for an enclosing module declaration."""
    module_raw: object
    async_reset_signals: frozenset[str] = frozenset()
    cache: dict[object, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ProceduralBlockFrame:
    """Strongly typed contextual data for an enclosing procedural block."""
    block_raw: object
    missing_sensitivity: dict[object, object] = field(default_factory=dict)
    mix_trigger: object | None = None
    multiple_nonblocking_write_triggers: dict[object, object] = field(default_factory=dict)
    is_comb: bool = False
    async_reset_names: frozenset[str] = frozenset()


@dataclass(frozen=True)
class CaseStatementFrame:
    """Strongly typed contextual data for an enclosing case statement."""
    case_raw: object
    fsm_model: object | None = None


class ContextFlag(Enum):

    # --- Timing / sensitivity ---
    HAS_EVENT_CONTROL = auto()
    POSEDGE = auto()
    NEGEDGE = auto()

    # --- Semantic classification ---
    ALWAYS = auto()        # always @(posedge/negedge ...)
    ALWAYS_FF = auto()
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

    def __init__(
        self,
        flags: set[ContextFlag] | None = None,
        scope: Scope | None = None,
        *,
        _parent: "Context | None" = None,
        _vnode: BaseVNode | None = None,
        data: dict[str, Any] | None = None,
        module_frame: ModuleFrame | None = None,
        block_frame: ProceduralBlockFrame | None = None,
        case_frame: CaseStatementFrame | None = None,
    ):
        self._parent = _parent
        self._vnode = _vnode
        self.flags = flags if flags is not None else set()
        self._scope = scope
        self.data = data if data is not None else {}
        self.module_frame = (
            module_frame
            if module_frame is not None
            else (_parent.module_frame if _parent is not None else None)
        )
        self.block_frame = (
            block_frame
            if block_frame is not None
            else (_parent.block_frame if _parent is not None else None)
        )
        self.case_frame = (
            case_frame
            if case_frame is not None
            else (_parent.case_frame if _parent is not None else None)
        )

    def iter_ancestors(self, include_self: bool = True) -> Iterator[BaseVNode]:
        """Iterate vnodes from current node up through ancestors towards the root."""
        node: "Context | None" = self
        depth = 0
        seen: set[int] = set()
        if not include_self and node is not None:
            seen.add(id(node))
            node = node._parent
        while node is not None and node._vnode is not None and depth < 256:
            node_id = id(node)
            if node_id in seen:
                break
            seen.add(node_id)
            depth += 1
            yield node._vnode
            node = node._parent

    def enclosing(
        self,
        predicate: Callable[[BaseVNode], bool],
        include_self: bool = False,
    ) -> BaseVNode | None:
        """Return the nearest enclosing ancestor vnode satisfying `predicate`."""
        for vnode in self.iter_ancestors(include_self=include_self):
            if predicate(vnode):
                return vnode
        return None

    @property
    def stack(self) -> list[BaseVNode]:
        """Ancestor chain from root to current node, rebuilt on demand from parent pointers."""
        nodes = list(self.iter_ancestors(include_self=True))
        nodes.reverse()
        return nodes

    def push(self, vnode: BaseVNode) -> "Context":
        return Context(
            flags=self.flags,
            scope=self._scope,
            data=self.data,
            _parent=self,
            _vnode=vnode,
            module_frame=self.module_frame,
            block_frame=self.block_frame,
            case_frame=self.case_frame,
        )

    def with_flag(self, flag: ContextFlag) -> "Context":
        return Context(
            flags=self.flags | {flag},
            scope=self._scope,
            data=self.data,
            _parent=self._parent,
            _vnode=self._vnode,
            module_frame=self.module_frame,
            block_frame=self.block_frame,
            case_frame=self.case_frame,
        )

    def has(self, flag: ContextFlag) -> bool:
        return flag in self.flags

    def with_scope(self, scope: Scope) -> "Context":
        return Context(
            flags=self.flags,
            scope=scope,
            data=self.data,
            _parent=self._parent,
            _vnode=self._vnode,
            module_frame=self.module_frame,
            block_frame=self.block_frame,
            case_frame=self.case_frame,
        )

    def with_data(self, key: str, value: Any) -> "Context":
        return Context(
            flags=self.flags,
            scope=self._scope,
            data={**self.data, key: value},
            _parent=self._parent,
            _vnode=self._vnode,
            module_frame=self.module_frame,
            block_frame=self.block_frame,
            case_frame=self.case_frame,
        )

    def with_module_frame(self, frame: ModuleFrame | None) -> "Context":
        new_data = {
            **self.data,
            "module_async_resets": set(frame.async_reset_signals) if frame else set(),
            "module_cache": frame.cache if frame else {},
        }
        return Context(
            flags=self.flags,
            scope=self._scope,
            data=new_data,
            _parent=self._parent,
            _vnode=self._vnode,
            module_frame=frame,
            block_frame=self.block_frame,
            case_frame=self.case_frame,
        )

    def with_block_frame(self, frame: ProceduralBlockFrame | None) -> "Context":
        new_data = {
            **self.data,
            "missing_sensitivity": frame.missing_sensitivity if frame else {},
            "mix_trigger": frame.mix_trigger if frame else None,
            "multiple_nonblocking_write_triggers": frame.multiple_nonblocking_write_triggers if frame else {},
            "comb_always_block": (frame.block_raw, frame.is_comb) if frame else None,
            "block_async_reset_names": (frame.block_raw, set(frame.async_reset_names)) if frame else None,
        }
        return Context(
            flags=self.flags,
            scope=self._scope,
            data=new_data,
            _parent=self._parent,
            _vnode=self._vnode,
            module_frame=self.module_frame,
            block_frame=frame,
            case_frame=self.case_frame,
        )

    def with_case_frame(self, frame: CaseStatementFrame | None) -> "Context":
        new_data = {
            **self.data,
            "fsm_model": (frame.case_raw, frame.fsm_model) if frame else None,
        }
        return Context(
            flags=self.flags,
            scope=self._scope,
            data=new_data,
            _parent=self._parent,
            _vnode=self._vnode,
            module_frame=self.module_frame,
            block_frame=self.block_frame,
            case_frame=frame,
        )

    def scope(self) -> Scope:
        if self._scope is None:
            raise RuntimeError("Context has no scope")
        return self._scope

    def __repr__(self) -> str:
        return f"stack: {self.stack} \nflags: {self.flags} \nscope: {self._scope}"
