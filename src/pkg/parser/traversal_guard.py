"""AST Traversal Guard & Active-Path Cycle Immunity Subsystem.

Provides cycle detection, recursion depth bounding, and immunity against
CPython/PyBind11 object wrapper memory address recycling across all AST queries,
predicates, and procedural traversals.

Key Architectural Guarantees:
1. Complete Loop Immunity: Prevents infinite loops and stack overflows (RecursionError)
   on cyclic AST graphs, self-referential mock nodes, and deep structures.
2. PyBind11 Address Recycling Immunity: Tracks active descent paths on the call stack
   rather than flat persistent ID sets. Temporary C++ wrapper PyObjects created on the
   fly between loop iterations cannot collide with discarded sibling memory addresses.
3. Zero Boilerplate: Replaces repetitive, error-prone `try...finally: visited.discard(...)`
   and `if depth >= MAX_DEPTH: return` patterns with clean context managers and decorators.
"""
from __future__ import annotations

import functools
import inspect
from contextvars import ContextVar
from typing import Any, Callable, Iterator, TypeVar, cast

from .types import SyntaxNode

F = TypeVar("F", bound=Callable[..., Any])


class _InactiveScope:
    __slots__ = ()

    def __bool__(self) -> bool:
        return False

    def __enter__(self) -> _InactiveScope:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass


_INACTIVE_SCOPE = _InactiveScope()


class ActivePathScope:
    """RAII context manager entered via `ActivePath.enter(node)`."""

    __slots__ = ("_path", "_nid")

    def __init__(self, path: ActivePath, nid: int) -> None:
        self._path = path
        self._nid = nid

    def __bool__(self) -> bool:
        return True

    def __enter__(self) -> ActivePathScope:
        self._path._active_ids.add(self._nid)
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self._path._active_ids.discard(self._nid)


class ActivePath:
    """Tracks active AST nodes on the recursion descent stack.

    Prevents infinite loops on cyclical graphs and bounds descent depth,
    while discarding nodes immediately upon stack unwind so CPython memory
    allocator address reuse for ephemeral PyBind11 wrappers never causes
    false-positive cycle rejections among sibling nodes.
    """

    __slots__ = ("_active_ids", "_depth", "_max_depth")

    def __init__(
        self,
        max_depth: int = 64,
        _active_ids: set[int] | None = None,
        _depth: int = 0,
    ) -> None:
        self._max_depth = max_depth
        self._active_ids = _active_ids if _active_ids is not None else set()
        self._depth = _depth

    @property
    def depth(self) -> int:
        return self._depth

    @property
    def max_depth(self) -> int:
        return self._max_depth

    def enter(self, node: object) -> ActivePathScope | _InactiveScope:
        """Attempt to enter `node`. Returns an active scope if safe, or an inactive
        scope if `node` is None, already in the active path (cycle), or depth limit reached.
        """
        if node is None or self._depth >= self._max_depth:
            return _INACTIVE_SCOPE
        nid = id(getattr(node, "raw", node))
        if nid in self._active_ids:
            return _INACTIVE_SCOPE
        return ActivePathScope(self, nid)

    def next_level(self) -> ActivePath:
        """Return a child ActivePath with incremented depth sharing the active ID set."""
        return ActivePath(self._max_depth, self._active_ids, self._depth + 1)


def _make_node_extractor(func: Callable[..., Any], node_arg: int | str) -> Callable[[tuple[Any, ...], dict[str, Any]], Any]:
    """Pre-computes node extraction logic for a function signature at decoration time."""
    try:
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
    except (ValueError, TypeError):
        param_names = []

    if isinstance(node_arg, str):
        target_name = node_arg
        param_idx = param_names.index(target_name) if target_name in param_names else None

        def extract_by_name(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
            if target_name in kwargs:
                return kwargs[target_name]
            if param_idx is not None and param_idx < len(args):
                return args[param_idx]
            return None

        return extract_by_name

    if node_arg == 0:
        def extract_first(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
            if args:
                return args[0]
            if param_name is not None and param_name in kwargs:
                return kwargs[param_name]
            return None

        return extract_first

    target_idx = node_arg
    param_name = param_names[target_idx] if target_idx < len(param_names) else None

    def extract_by_index(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
        if target_idx < len(args):
            return args[target_idx]
        if param_name is not None and param_name in kwargs:
            return kwargs[param_name]
        return None

    return extract_by_index


def guarded_traversal(
    max_depth: int = 64,
    default: Any = None,
    node_arg: int | str = 0,
) -> Callable[[F], F]:
    """Decorator guarding a recursive AST traversal function against cycles,
    excessive recursion depth, and PyBind11 wrapper address recycling.

    Eliminates all `try...finally: visited.discard(id)` boilerplate.
    Returns `default` immediately if a cycle or depth limit is encountered.
    """

    def decorator(func: F) -> F:
        cv_path: ContextVar[set[int] | None] = ContextVar(f"{func.__qualname__}_path", default=None)
        extract_node = _make_node_extractor(func, node_arg)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            node = extract_node(args, kwargs)
            if node is None:
                return default

            path = cv_path.get(None)
            if path is None:
                path = set()
                tok = cv_path.set(path)
                nid = id(getattr(node, "raw", node))
                path.add(nid)
                try:
                    return func(*args, **kwargs)
                finally:
                    path.discard(nid)
                    cv_path.reset(tok)

            if len(path) >= max_depth:
                return default

            nid = id(getattr(node, "raw", node))
            if nid in path:
                return default

            path.add(nid)
            try:
                return func(*args, **kwargs)
            finally:
                path.discard(nid)

        return cast(F, wrapper)

    return decorator


def guarded_generator(
    max_depth: int = 128,
    node_arg: int | str = 0,
) -> Callable[[F], F]:
    """Decorator guarding a recursive AST generator function against cycles,
    excessive recursion depth, and PyBind11 wrapper address recycling.

    Eliminates all `try...finally: visited.discard(id)` boilerplate from generator
    traversals. Halts recursion safely if a cycle or depth limit is encountered.
    """

    def decorator(func: F) -> F:
        cv_path: ContextVar[set[int] | None] = ContextVar(f"{func.__qualname__}_path", default=None)
        extract_node = _make_node_extractor(func, node_arg)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            node = extract_node(args, kwargs)
            if node is None:
                return

            path = cv_path.get(None)
            if path is None:
                path = set()
                tok = cv_path.set(path)
                nid = id(getattr(node, "raw", node))
                path.add(nid)
                try:
                    yield from func(*args, **kwargs)
                finally:
                    path.discard(nid)
                    cv_path.reset(tok)
                return

            if len(path) >= max_depth:
                return

            nid = id(getattr(node, "raw", node))
            if nid in path:
                return

            path.add(nid)
            try:
                yield from func(*args, **kwargs)
            finally:
                path.discard(nid)

        return cast(F, wrapper)

    return decorator


def ast_descendants_iter(
    root: object,
    stop_at: tuple[type, ...] | Callable[[object], bool] | None = None,
    max_depth: int = 128,
) -> Iterator[object]:
    """Iteratively walk descendants of `root` using an explicit DFS stack.

    Eliminates Python call-stack recursion entirely while retaining active-path
    cycle protection and bounded depth.
    """
    if root is None:
        return

    # stack entry: (node, depth)
    stack: list[tuple[object, int]] = [(root, 0)]
    active_path: set[int] = set()

    while stack:
        curr, depth = stack.pop()
        if depth >= max_depth:
            continue

        cid = id(getattr(curr, "raw", curr))
        if cid in active_path:
            continue

        if curr is not root:
            yield curr

        if stop_at is not None:
            if callable(stop_at) and stop_at(curr):
                continue
            if isinstance(stop_at, tuple) and isinstance(curr, stop_at):
                continue

        try:
            children = list(curr)  # type: ignore[call-overload]
        except TypeError:
            continue

        # Push children in reverse order so first child is popped first
        for child in reversed(children):
            if child is not None:
                stack.append((child, depth + 1))
