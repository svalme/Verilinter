from typing import TYPE_CHECKING

from ...parser.syntax import is_concurrent_assertion_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoConcurrentAssertionRule(Rule):
    code = "NO_CONCURRENT_ASSERTION"
    message = "Use of concurrent assertions (assert/assume/cover property) is discouraged in synthesizable RTL; assertions belong in verification, not design"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_concurrent_assertion_node(vnode.raw)
