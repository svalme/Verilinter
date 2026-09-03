from typing import TYPE_CHECKING

from ...parser.syntax import is_display_system_task
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoDisplaySystemTaskRule(Rule):
    code = "NO_DISPLAY_SYSTEM_TASK"
    message = "Use of $display/$write/$monitor/$strobe-family system tasks is discouraged in synthesizable RTL; these are simulation-only debug output"
    category = "classic_rtl_exclusion"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_display_system_task(vnode.raw)
