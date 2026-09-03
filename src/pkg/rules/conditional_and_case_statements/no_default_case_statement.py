from typing import TYPE_CHECKING

from ...parser.syntax import enclosing_case_statement, has_default_case_item, is_endcase_token
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoDefaultCaseStatementRule(Rule):
    code = "NO_DEFAULT_CASE_STATEMENT"
    message = "Case statement missing default case"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if not is_endcase_token(vnode.raw):
            return False

        case_statement = enclosing_case_statement(ctx)
        if case_statement is None:
            return False

        return not has_default_case_item(case_statement.raw)
