from typing import TYPE_CHECKING

from ...parser.syntax import is_always_latch_block
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoAlwaysLatchRule(Rule):
    code = "NO_ALWAYS_LATCH"
    message = "Use of always_latch can hide unintended latch-oriented design choices"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_always_latch_block(vnode.raw)
