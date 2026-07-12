from ...parser.syntax import is_always_latch_block
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoAlwaysLatchRule(Rule):
    code = "NO_ALWAYS_LATCH"
    message = "Use of always_latch can hide unintended latch-oriented design choices"

    def applies(self, vnode, ctx) -> bool:
        return is_always_latch_block(vnode.raw)
