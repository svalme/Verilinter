from typing import TYPE_CHECKING

from ...parser.syntax import is_delay_control_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoDelayControlRule(Rule):
    code = "NO_DELAY_CONTROL"
    message = "Use of delay controls (#delay) is discouraged in synthesizable RTL; delays are simulation-only timing"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_delay_control_node(vnode.raw)
