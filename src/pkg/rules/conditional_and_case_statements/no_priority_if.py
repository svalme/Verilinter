from typing import TYPE_CHECKING

from ...parser.syntax import is_priority_if_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoPriorityIfRule(Rule):
    code = "NO_PRIORITY_IF"
    message = "Use of priority if can overstate branch ordering assumptions"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_priority_if_token(vnode.raw, ctx)
