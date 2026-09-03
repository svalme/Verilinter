from typing import TYPE_CHECKING

from ...parser.syntax import is_expect_restrict_property_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoExpectRestrictPropertyRule(Rule):
    code = "NO_EXPECT_RESTRICT_PROPERTY"
    message = "Use of expect/restrict property statements is discouraged in synthesizable RTL; assertions belong in verification, not design"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_expect_restrict_property_node(vnode.raw)
