from ...parser.syntax import is_case_generate_node
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoCaseGenerateRule(Rule):
    code = "NO_CASE_GENERATE"
    message = "Use of case generate can make structural intent harder to follow"

    def applies(self, vnode, ctx) -> bool:
        return is_case_generate_node(vnode.raw)
