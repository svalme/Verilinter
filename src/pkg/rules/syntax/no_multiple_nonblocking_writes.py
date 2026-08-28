from ...parser.syntax import is_assignment_expression
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from .rule_runner import rule_runner


@rule_runner.register
class NoMultipleNonblockingWritesRule(Rule):
    code = "NO_MULTIPLE_NONBLOCKING_WRITES"
    message = "Multiple non-blocking writes to the same target in one procedural block"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: object) -> bool:
        if not is_assignment_expression(vnode.raw):
            return False

        triggers = getattr(ctx, "data", {}).get("multiple_nonblocking_write_triggers", {})
        return vnode.raw in triggers.values()
