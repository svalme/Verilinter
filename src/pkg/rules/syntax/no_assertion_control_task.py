from typing import TYPE_CHECKING

from ...parser.syntax import is_assertion_control_task
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoAssertionControlTaskRule(Rule):
    code = "NO_ASSERTION_CONTROL_TASK"
    message = "Use of $assertoff/$asserton/$assertkill-family assertion-control system tasks is discouraged in synthesizable RTL; these are simulation-only verification controls"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_assertion_control_task(vnode.raw)
