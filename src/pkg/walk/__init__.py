"""The traversal engine: Walker drives a recursive walk over the syntax tree,
Dispatch maps raw pyslang node types to handler instances, and Context is the
immutable per-node snapshot of traversal state (ancestor stack, flags, scope).
"""
