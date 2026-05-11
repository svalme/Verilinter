# vnode/identifier_vnode.py
import pyslang as sl

from ..vnodes.syntax_vnode import SyntaxVNode
from .vnode_factory import vnode_factory

@vnode_factory.register(sl.IdentifierNameSyntax)
class IdentifierNameVNode(SyntaxVNode):

    def __init__(self, raw: sl.SyntaxNode, tree: sl.SyntaxTree):
        super().__init__(raw, tree)

    @property
    def identifier_name(self) -> str:
        return self.raw.identifier.value

    @property
    def raw_children(self) -> list:
        if hasattr(self.raw, 'identifier') and self.raw.identifier is not None:
            return [self.raw.identifier]
        return []
