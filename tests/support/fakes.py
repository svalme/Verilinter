"""Lightweight stand-ins for pyslang nodes and vnodes.

`FakeNode` raises `AttributeError` for any field that was not set, so
`getattr(raw, "field", None)` in parser helpers yields `None` as it does on a
real pyslang node. A bare `Mock` returns a truthy child `Mock` there instead,
which hides a helper that starts reading a field the test never set.
"""
from __future__ import annotations

from typing import Iterator

from src.pkg.vnodes.base_vnode import BaseVNode


class FakeNode:
    def __init__(self, kind: object, *, children: tuple["FakeNode", ...] = (), **fields: object) -> None:
        self.kind = kind
        self.parent: FakeNode | None = None
        self._children = list(children)
        for child in self._children:
            child.parent = self
        self.__dict__.update(fields)

    def __iter__(self) -> Iterator["FakeNode"]:
        return iter(self._children)

    def __repr__(self) -> str:
        return f"FakeNode({self.kind})"


class FakeVNode(BaseVNode):
    """A real `BaseVNode`, so `isinstance` checks and `Context.push` behave normally."""

    def __init__(self, raw: object, tree: object = None, location: object = None) -> None:
        super().__init__(raw, tree)  # type: ignore[arg-type]
        self._location = location

    def snippet(self) -> str:
        return ""

    @property
    def location(self) -> object:
        return self._location

    @location.setter
    def location(self, value: object) -> None:
        self._location = value


def fake_vnode(kind: object, location: object = None, **fields: object) -> FakeVNode:
    return FakeVNode(FakeNode(kind, **fields), location=location)


__all__ = ["FakeNode", "FakeVNode", "fake_vnode"]
