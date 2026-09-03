from typing import TYPE_CHECKING

from ...parser.syntax import is_simulation_control_task
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoSimulationControlTaskRule(Rule):
    code = "NO_SIMULATION_CONTROL_TASK"
    message = "Use of $stop/$finish is discouraged in synthesizable RTL; these are simulation-only control tasks"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_simulation_control_task(vnode.raw)
