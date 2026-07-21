from ...parser.syntax import is_supply0_supply1_token
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoSupply0Supply1Rule(Rule):
    code = "NO_SUPPLY0_SUPPLY1"
    message = "Use of supply0/supply1 is discouraged in RTL; prefer explicit constant-driving intent instead"

    def applies(self, vnode, ctx) -> bool:
        return is_supply0_supply1_token(vnode.raw)
