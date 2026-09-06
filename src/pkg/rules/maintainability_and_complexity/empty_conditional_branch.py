from typing import TYPE_CHECKING

from ...parser.syntax import is_empty_conditional_or_case_branch
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class EmptyConditionalBranchRule(Rule):
    code = "EMPTY_CONDITIONAL_BRANCH"
    message = "if/else branch or case item body is empty"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, _ctx: "Context") -> bool:
        return is_empty_conditional_or_case_branch(vnode.raw)
