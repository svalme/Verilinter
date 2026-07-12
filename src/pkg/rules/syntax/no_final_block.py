from ...parser.syntax import is_final_block
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoFinalBlockRule(Rule):
    code = "NO_FINAL_BLOCK"
    message = "Use of final blocks is usually not appropriate in synthesizable RTL"

    def applies(self, vnode, ctx) -> bool:
        return is_final_block(vnode.raw)
