from abc import ABC, abstractmethod
from typing import TypedDict, NotRequired

from ..parser.types import RawNode, SyntaxTree


class Location(TypedDict):
    line: int
    col: int
    file: NotRequired[str]


class BaseVNode(ABC):
    def __init__(self, raw: RawNode, tree: SyntaxTree):
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
