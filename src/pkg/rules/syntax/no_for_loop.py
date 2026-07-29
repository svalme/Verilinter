from typing import TYPE_CHECKING

from ...parser.syntax import is_plain_for_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoForLoopRule(Rule):
    code = "NO_FOR_LOOP"
    message = "Use of for loops is discouraged in synthesizable RTL"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_plain_for_token(vnode.raw, ctx)
