from typing import TYPE_CHECKING

from ...parser.syntax import is_assign_deassign_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoAssignDeassignRule(Rule):
    code = "NO_ASSIGN_DEASSIGN"
    message = "Use of assign/deassign is discouraged in RTL; prefer explicit continuous or procedural intent"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_assign_deassign_token(vnode.raw)
