"""Per-module memoization keyed by syntax node identity.

pyslang hands out short-lived Python wrappers, so a bare ``id(node)`` key can
be reused by a different node once the first wrapper is collected, returning
another node's cached result. Entries therefore hold the node itself, which
keeps its ``id`` from being reused for the cache's lifetime, and a hit is
accepted only when the stored node is the queried node.
"""

from __future__ import annotations

MISSING: object = object()


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
