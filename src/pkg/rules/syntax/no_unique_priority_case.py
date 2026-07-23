from typing import TYPE_CHECKING

from ...parser.syntax import is_unique_priority_case_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoUniquePriorityCaseRule(Rule):
    code = "NO_UNIQUE_PRIORITY_CASE"
    message = "Use of unique/priority case can overstate case completeness or exclusivity"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_unique_priority_case_token(vnode.raw)
