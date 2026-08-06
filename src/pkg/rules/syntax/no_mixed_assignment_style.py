from typing import TYPE_CHECKING

from ...parser.syntax import is_assignment_expression
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoMixedAssignmentStyleRule(Rule):
    code = "NO_MIXED_ASSIGNMENT_STYLE"
    message = "Mixed blocking and non-blocking assignments used in the same procedural block"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if not is_assignment_expression(vnode.raw):
            return False

        # Computed once per enclosing block by ProceduralBlockHandler rather
        # than re-derived here per node.
        return ctx.data.get("mix_trigger") is vnode.raw
