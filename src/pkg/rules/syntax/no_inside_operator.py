from typing import TYPE_CHECKING

from ...parser.syntax import is_inside_operator_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoInsideOperatorRule(Rule):
    code = "NO_INSIDE_OPERATOR"
    message = "Use of the inside operator is discouraged in this RTL subset"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_inside_operator_token(vnode.raw, vnode.tree)
