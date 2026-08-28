# src/pkg/vnode/token_vnode.py

from .base_vnode import BaseVNode, Location
from ..parser.syntax import token_location, token_raw_text
from ..parser.types import SyntaxTree, Token

class TokenVNode(BaseVNode):
    def __init__(self, raw: Token, tree: SyntaxTree) -> None:
        super().__init__(raw, tree)

    @property
    def location(self) -> Location:
        return token_location(self.raw, self.tree)

    def snippet(self) -> str:
        return token_raw_text(self.raw)

    def __repr__(self) -> str:
        loc = self.location
        loc_str = f"{loc['line']}:{loc['col']}" if loc else "?:?"
        return f"TokenVNode {self.raw.kind.name} '{self.snippet()}' @ {loc_str}"


