from typing import TYPE_CHECKING

from ...parser.syntax import is_unique_if_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoUniqueIfRule(Rule):
    code = "NO_UNIQUE_IF"
    message = "Use of unique if can overstate branch exclusivity assumptions"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_unique_if_token(vnode.raw, ctx)
