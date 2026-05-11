from abc import ABC, abstractmethod
from typing import TypedDict, NotRequired
import pyslang as sl


class Location(TypedDict):
    line: int
    col: int
    file: NotRequired[str]


class BaseVNode(ABC):
    def __init__(self, raw: sl.SyntaxNode | sl.Token, tree: sl.SyntaxTree):
        self.raw = raw
        self.tree = tree

    @abstractmethod
    def snippet(self) -> str: ...

    @property
    def location(self) -> Location:
        return {"line": 0, "col": 0}

    @property
    def raw_children(self) -> list:
        return []