from typing import TYPE_CHECKING

from ...parser.syntax import is_always_ff_block
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoAlwaysFFRule(Rule):
    code = "NO_ALWAYS_FF"
    message = "Use of always_ff is discouraged in this RTL subset"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_always_ff_block(vnode.raw)
