from typing import TYPE_CHECKING

from ...parser.syntax import is_do_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoDoWhileLoopRule(Rule):
    code = "NO_DO_WHILE_LOOP"
    message = "Use of do-while loops is discouraged in synthesizable RTL"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_do_token(vnode.raw)
