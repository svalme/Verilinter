from ...parser.syntax import is_initial_block
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoInitialBlockRule(Rule):
    code = "NO_INITIAL_BLOCK"
    message = "Use of initial blocks can be unsafe in synthesizable RTL"

    def applies(self, vnode, ctx) -> bool:
        return is_initial_block(vnode.raw)
