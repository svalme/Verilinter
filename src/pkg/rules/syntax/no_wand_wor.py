from ...parser.syntax import is_wand_wor_token
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoWandWorRule(Rule):
    code = "NO_WAND_WOR"
    message = "Use of wand/wor is discouraged in RTL; prefer explicit logic composition instead"

    def applies(self, vnode, ctx) -> bool:
        return is_wand_wor_token(vnode.raw)
