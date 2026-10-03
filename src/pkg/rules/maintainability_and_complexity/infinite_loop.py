from typing import TYPE_CHECKING

from ...parser.syntax import is_infinite_loop
from ...parser.types import (
    DoWhileStatementNode,
    ForLoopStatementNode,
    ForeverStatementNode,
    LoopStatementNode,
)
from ...vnodes.base_vnode import BaseVNode
from ..base_rule import Rule
from ..rule_runner import rule_runner

if TYPE_CHECKING:
    from ...walk.context import Context


@rule_runner.register
class InfiniteLoopRule(Rule):
    code = "INFINITELOOP"
    message = "Infinite loop condition is always true and lacks exit or timing control"
    category = "rtl_correctness"
    default_profiles = ("rtl_strict", "sv_rtl_subset", "legacy_verilog")
    target_node_types = (
        ForeverStatementNode,
        LoopStatementNode,
        DoWhileStatementNode,
        ForLoopStatementNode,
    )

    def applies(self, vnode: BaseVNode, ctx: "Context") -> bool:
        try:
            scope = ctx.scope()
        except Exception:
            scope = None
        return is_infinite_loop(vnode.raw, scope=scope)
