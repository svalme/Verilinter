# vnode/identifier_vnode.py
import pyslang as sl

from ..vnodes.syntax_vnode import SyntaxVNode
from .vnode_factory import vnode_factory
from .token_vnode import TokenVNode

@vnode_factory.register(sl.IdentifierNameSyntax)
class IdentifierNameVNode(SyntaxVNode):
    """Specialized node for identifier tokens"""

    def __init__(self, raw: sl.SyntaxNode, tree: sl.SyntaxTree):
        super().__init__(raw, tree)

    @property
    def identifier_name(self) -> str:
        """Get identifier name"""
        return self.raw.identifier.value
    
    @property
    def children(self) -> list:
        """Ensure the identifier token is exposed as a child vnode."""
        out = []
        if hasattr(self.raw, 'identifier') and self.raw.identifier is not None:
            out.append(TokenVNode(self.raw.identifier, self.tree))
        return out
    
   