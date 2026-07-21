from ...parser.syntax import is_defparam_token
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoDefparamRule(Rule):
    code = "NO_DEFPARAM"
    message = "Use of defparam is discouraged; prefer explicit parameter overrides at instantiation"

    def applies(self, vnode, ctx) -> bool:
        return is_defparam_token(vnode.raw)
