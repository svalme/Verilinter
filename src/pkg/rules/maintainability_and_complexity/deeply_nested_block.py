from typing import TYPE_CHECKING

from ...parser.syntax import is_block_statement, procedural_nesting_depth
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context

_MAX_NESTING_DEPTH = 4


@rule_runner.register
class DeeplyNestedBlockRule(Rule):
    """Flags a `begin...end` block whose nesting (via begin/end, `if`, and
    `case` ancestors within one procedural block) first crosses
    `_MAX_NESTING_DEPTH`. Deliberately fires only on the block that first
    crosses the threshold, not every deeper block nested inside it too --
    avoids cascading duplicate noise on one over-nested region. Loop
    statements (`for`/`while`/`repeat`/`forever`) are not counted toward
    depth.
    """

    code = "DEEPLY_NESTED_BLOCK"
    message = f"Procedural block/conditional/case nesting exceeds {_MAX_NESTING_DEPTH} levels; consider refactoring"
    category = "rtl_style"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        if not is_block_statement(vnode.raw):
            return False
        return procedural_nesting_depth(ctx) + 1 == _MAX_NESTING_DEPTH + 1
