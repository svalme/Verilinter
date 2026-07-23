from typing import TYPE_CHECKING

from ...parser.syntax import is_supply0_supply1_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoSupply0Supply1Rule(Rule):
    code = "NO_SUPPLY0_SUPPLY1"
    message = "Use of supply0/supply1 is discouraged in RTL; prefer explicit constant-driving intent instead"

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        return is_supply0_supply1_token(vnode.raw)
