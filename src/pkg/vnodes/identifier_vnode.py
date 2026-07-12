# vnode/identifier_vnode.py
from ..parser.types import IdentifierNameNode, IdentifierSelectNameNode, SyntaxNode, SyntaxTree
from ..vnodes.syntax_vnode import SyntaxVNode
from .vnode_factory import vnode_factory

@vnode_factory.register(IdentifierNameNode)
@vnode_factory.register(IdentifierSelectNameNode)
class IdentifierNameVNode(SyntaxVNode):

    def __init__(self, raw: SyntaxNode, tree: SyntaxTree):
        super().__init__(raw, tree)

    @property
    def identifier_name(self) -> str:
        return self.raw.identifier.value

    @property
    def raw_children(self) -> list:
        children = list(self.raw.__iter__())
        return children if children else []
