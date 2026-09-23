from abc import ABC, abstractmethod
from typing import TypedDict, NotRequired

from ..parser.types import RawNode, SyntaxTree


class Location(TypedDict, total=False):
    line: int
    col: int
    file: str


class BaseVNode(ABC):
    def __init__(self, raw: RawNode, tree: SyntaxTree) -> None:
        self.raw = raw
        self.tree = tree

    @abstractmethod
    def snippet(self) -> str: ...

    @property
    def location(self) -> Location | None:
        return None

    @property
    def raw_children(self) -> list[RawNode]:
        return []
