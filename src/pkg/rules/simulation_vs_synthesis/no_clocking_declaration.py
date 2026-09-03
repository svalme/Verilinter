from typing import TYPE_CHECKING

from ...parser.syntax import is_clocking_declaration_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoClockingDeclarationRule(Rule):
    code = "NO_CLOCKING_DECLARATION"
    message = "Use of clocking declarations is discouraged in synthesizable RTL"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_clocking_declaration_node(vnode.raw)
