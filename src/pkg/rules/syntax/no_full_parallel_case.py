from ...parser.syntax import has_full_parallel_case_pragma, is_case_keyword_token
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoFullParallelCaseRule(Rule):
    code = "NO_FULL_PARALLEL_CASE"
    message = "Use of full_case / parallel_case pragmas can hide real case coverage issues"

    def applies(self, vnode, ctx) -> bool:
        return is_case_keyword_token(vnode.raw) and has_full_parallel_case_pragma(vnode.raw, vnode.tree)
