from typing import TypedDict
import pyslang as sl


class Location(TypedDict):
    line: int
    col: int


class BaseVNode:
    def __init__(self, raw: sl.SyntaxNode | sl.Token, tree: sl.SyntaxTree):
        self.raw = raw
        self.tree = tree

    def snippet(self) -> str:
        raise NotImplementedError

    @property
    def location(self) -> Location:
        return {"line": 0, "col": 0}

    @property
    def children(self) -> list[BaseVNode]:
        return []  