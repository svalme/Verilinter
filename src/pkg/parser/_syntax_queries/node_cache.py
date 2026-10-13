"""Per-module memoization keyed by syntax node identity.

pyslang hands out short-lived Python wrappers, so a bare ``id(node)`` key can
be reused by a different node once the first wrapper is collected, returning
another node's cached result. Entries therefore hold the node itself, which
keeps its ``id`` from being reused for the cache's lifetime, and a hit is
accepted only when the stored node is the queried node.
"""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, TypeVar

MISSING: object = object()

F = TypeVar("F", bound=Callable[..., Any])



def node_cache_get(cache: dict[object, object] | None, tag: str, node: object) -> object:
    """Return the value stored for ``node`` under ``tag``, else ``MISSING``."""
    if cache is None:
        return MISSING
    entry = cache.get((tag, id(node)))
    if isinstance(entry, tuple) and len(entry) == 2 and entry[0] is node:
        return entry[1]
    return MISSING


def node_cache_put(cache: dict[object, object] | None, tag: str, node: object, value: object) -> None:
    if cache is not None:
        cache[(tag, id(node))] = (node, value)


def extract_module_cache(obj: object) -> dict[object, object] | None:
    """Extract a module cache dictionary from a dict, Context, or frame object."""
    if isinstance(obj, dict):
        return obj
    module_frame = getattr(obj, "module_frame", None)
    if module_frame is not None and isinstance(module_frame.cache, dict):
        return module_frame.cache
    data = getattr(obj, "data", None)
    if isinstance(data, dict):
        cache = data.get("module_cache")
        if isinstance(cache, dict):
            return cache
    return None


def memoized_node_query(
    tag: str,
    node_arg: int | str = 0,
    ctx_arg: int | str | None = None,
) -> Callable[[F], F]:
    """Decorator memoizing AST syntax queries per module cache.

    Guarantees immunity against PyBind11 object address recycling by binding
    the cached node instance to the lifetime of the cache entry.

    Extracts the syntax node (unwrapping `raw` if a VNode adapter is provided)
    and resolves the cache dictionary from the invocation arguments.
    """
    def decorator(func: F) -> F:
        param_names: list[str] = []
        try:
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
        except (ValueError, TypeError):
            pass

        def _get_node(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
            val = None
            if isinstance(node_arg, str):
                if node_arg in kwargs:
                    val = kwargs[node_arg]
                elif node_arg in param_names:
                    idx = param_names.index(node_arg)
                    if idx < len(args):
                        val = args[idx]
            elif isinstance(node_arg, int):
                if node_arg < len(args):
                    val = args[node_arg]
                elif param_names and node_arg < len(param_names) and param_names[node_arg] in kwargs:
                    val = kwargs[param_names[node_arg]]
            if val is not None:
                return getattr(val, "raw", val)
            return None

        def _get_cache(args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[object, object] | None:
            if ctx_arg is not None:
                val = None
                if isinstance(ctx_arg, str):
                    if ctx_arg in kwargs:
                        val = kwargs[ctx_arg]
                    elif ctx_arg in param_names:
                        idx = param_names.index(ctx_arg)
                        if idx < len(args):
                            val = args[idx]
                elif isinstance(ctx_arg, int):
                    if ctx_arg < len(args):
                        val = args[ctx_arg]
                    elif param_names and ctx_arg < len(param_names) and param_names[ctx_arg] in kwargs:
                        val = kwargs[param_names[ctx_arg]]
                if val is not None:
                    return extract_module_cache(val)
            for kw in ("cache", "ctx", "context"):
                if kw in kwargs:
                    c = extract_module_cache(kwargs[kw])
                    if c is not None:
                        return c
            for arg in args:
                c = extract_module_cache(arg)
                if c is not None:
                    return c
            return None

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            node = _get_node(args, kwargs)
            if node is None:
                return func(*args, **kwargs)

            cache = _get_cache(args, kwargs)
            if cache is None:
                return func(*args, **kwargs)

            cached = node_cache_get(cache, tag, node)
            if cached is not MISSING:
                return cached

            res = func(*args, **kwargs)
            node_cache_put(cache, tag, node, res)
            return res

        return wrapper  # type: ignore[return-value]

    return decorator

