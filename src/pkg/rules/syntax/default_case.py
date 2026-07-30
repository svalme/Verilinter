from ...parser.syntax import is_endcase_token
from ...vnodes.base_vnode import BaseVNode
from ...walk.context import Context, ContextFlag
from ..base_rule import Rule
from .rule_runner import rule_runner

@rule_runner.register
class DefaultCaseRule(Rule):
    code = "DEFAULT_CASE"
    message = "Case statement missing default case"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: Context) -> bool:
        return is_endcase_token(vnode.raw) \
            and ctx.has(ContextFlag.CASE_GENERATE) \
            and not ctx.has(ContextFlag.DEFAULT)
