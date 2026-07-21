from ...parser.syntax import is_force_release_token
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoForceReleaseRule(Rule):
    code = "NO_FORCE_RELEASE"
    message = "Use of force/release is discouraged in RTL; prefer explicit structural or procedural intent"

    def applies(self, vnode, ctx) -> bool:
        return is_force_release_token(vnode.raw)
