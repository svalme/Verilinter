from typing import TYPE_CHECKING

from ...parser.syntax import is_interface_declaration_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoInterfaceDeclarationRule(Rule):
    code = "NO_INTERFACE_DECLARATION"
    message = "Use of interface declarations is discouraged in synthesizable RTL"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_interface_declaration_node(vnode.raw)
