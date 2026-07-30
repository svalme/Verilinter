from typing import TYPE_CHECKING

from ...parser.syntax import is_primitive_declaration_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoPrimitiveDeclarationRule(Rule):
    code = "NO_PRIMITIVE_DECLARATION"
    message = "Use of user-defined primitive (UDP) declarations is discouraged in synthesizable RTL"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_primitive_declaration_node(vnode.raw)
