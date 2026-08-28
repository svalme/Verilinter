from .base_vnode import BaseVNode, Location
from ..parser.syntax import node_location, raw_node_children, syntax_node_snippet
from ..parser.types import RawNode, SyntaxNode, SyntaxTree

class SyntaxVNode(BaseVNode):
    def __init__(self, raw: SyntaxNode, tree: SyntaxTree) -> None:
        super().__init__(raw, tree)

    @property
    def kind(self) -> object:
        return self.raw.kind

    def snippet(self) -> str:
        return syntax_node_snippet(self.raw)

    def __repr__(self) -> str:
        loc = self.location
        loc_str = f"{loc['line']}:{loc['col']}" if loc else "?:?"
        return f"SyntaxVNode {self.raw.kind.name} @ {loc_str}"

    @property
    def location(self) -> Location:
        return node_location(self.raw, self.tree)

    @property
    def children(self) -> list[RawNode]:
        return self.raw_children

    @property
    def raw_children(self) -> list[RawNode]:
        return raw_node_children(self.raw)
