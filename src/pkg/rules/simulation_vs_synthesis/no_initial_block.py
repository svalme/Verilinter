from typing import TYPE_CHECKING

from ...parser.syntax import is_initial_block
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoInitialBlockRule(Rule):
    code = "NO_INITIAL_BLOCK"
    message = "Use of initial blocks can be unsafe in synthesizable RTL"
    category = "rtl_subset"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_initial_block(vnode.raw)
