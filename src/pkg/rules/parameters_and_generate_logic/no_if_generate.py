from typing import TYPE_CHECKING

from ...parser.syntax import is_if_generate_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoIfGenerateRule(Rule):
    code = "NO_IF_GENERATE"
    message = "Use of if-generate can make structural intent harder to follow"
    category = "rtl_subset"
    default_profiles = ("rtl_strict", "sv_rtl_subset")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_if_generate_node(vnode.raw)
