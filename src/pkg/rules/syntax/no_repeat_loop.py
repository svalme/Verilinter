from typing import TYPE_CHECKING

from ...parser.syntax import is_repeat_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoRepeatLoopRule(Rule):
    code = "NO_REPEAT_LOOP"
    message = "Use of repeat loops is discouraged in synthesizable RTL"
    category = "rtl_subset"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_repeat_token(vnode.raw)
