from typing import TYPE_CHECKING

from ...parser.syntax import is_case_generate_node
from ...parser.types import CaseGenerateNode
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoCaseGenerateRule(Rule):
    code = "NO_CASE_GENERATE"
    message = "Use of case generate can make structural intent harder to follow"
    category = "rtl_subset"
    default_profiles = ("rtl_strict", "sv_rtl_subset")
    target_node_types = (CaseGenerateNode,)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_case_generate_node(vnode.raw)
