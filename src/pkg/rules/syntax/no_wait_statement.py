from typing import TYPE_CHECKING

from ...parser.syntax import is_wait_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoWaitStatementRule(Rule):
    code = "NO_WAIT_STATEMENT"
    message = "Use of wait statements is discouraged in synthesizable RTL"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_wait_token(vnode.raw)
