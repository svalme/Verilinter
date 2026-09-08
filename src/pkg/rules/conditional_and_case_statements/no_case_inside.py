from typing import TYPE_CHECKING

from ...parser.syntax import is_case_inside_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoCaseInsideRule(Rule):
    code = "NO_CASE_INSIDE"
    message = "Use of case inside is discouraged in this RTL subset"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_case_inside_token(vnode.raw, ctx)
