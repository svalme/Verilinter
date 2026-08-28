from typing import TYPE_CHECKING

from ...parser.syntax import is_randsequence_statement_node
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoRandsequenceRule(Rule):
    code = "NO_RANDSEQUENCE"
    message = "Use of randsequence blocks is discouraged in synthesizable RTL; randsequence is a verification-oriented control construct"
    category = "sv_subset"
    default_profiles = ("sv_rtl_subset",)

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_randsequence_statement_node(vnode.raw)
