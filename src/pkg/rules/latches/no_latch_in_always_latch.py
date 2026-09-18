from typing import TYPE_CHECKING

from ...parser.syntax import is_always_latch_block, procedural_block_statement
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner
from ..combinational_logic.no_latch_in_always_comb import has_latch_pattern

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class NoLatchInAlwaysLatchRule(Rule):
    code = "NO_LATCH_IN_ALWAYS_LATCH"
    message = "No latches detected in always_latch block; block specifies complete combinational logic without latch-like storage"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if not is_always_latch_block(vnode.raw):
            return False

        statement = procedural_block_statement(vnode.raw)
        if statement is None:
            return False

        return not has_latch_pattern(statement)
