from typing import TYPE_CHECKING

from ...parser.syntax import is_unique0_case_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoUnique0CaseRule(Rule):
    code = "NO_UNIQUE0_CASE"
    message = "Use of unique0 case can overstate case coverage assumptions"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_unique0_case_token(vnode.raw, ctx)
