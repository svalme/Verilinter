# vnode/identifier_vnode.py
from ..parser.syntax import identifier_name, raw_node_children
from ..parser.types import IDENTIFIER_NAME_NODE_TYPES, RawNode, SyntaxNode, SyntaxTree
from ..vnodes.syntax_vnode import SyntaxVNode
from .vnode_factory import vnode_factory

class IdentifierNameVNode(SyntaxVNode):
    def __init__(self, raw: SyntaxNode, tree: SyntaxTree) -> None:
        super().__init__(raw, tree)

    @property
    def identifier_name(self) -> str:
        return identifier_name(self.raw) or ""

    @property
    def raw_children(self) -> list[RawNode]:
        return raw_node_children(self.raw)


for _raw_type in IDENTIFIER_NAME_NODE_TYPES:
    vnode_factory.register(_raw_type)(IdentifierNameVNode)
