from ..walk.context import Context, ContextFlag
from ..semantic.symbol_table import SymbolTable
from .syntax_node_handler import SyntaxNodeHandler
from ..vnodes.syntax_vnode import SyntaxVNode

from ..parser.syntax import (
    ALWAYS_BLOCK_KIND,
    ALWAYS_COMB_BLOCK_KIND,
    ALWAYS_LATCH_BLOCK_KIND,
    missing_sensitivity_trigger_nodes,
    mixed_assignment_trigger_node,
)
from ..parser.types import (
    ProceduralBlockNode,
)
from ..walk.dispatch import dispatch

@dispatch.register(ProceduralBlockNode)
class ProceduralBlockHandler(SyntaxNodeHandler):
    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        ctx = ctx.push(vnode)
        kind = vnode.kind

        if kind == ALWAYS_COMB_BLOCK_KIND:
            ctx = ctx.with_flag(ContextFlag.ALWAYS_COMB)

        elif kind == ALWAYS_BLOCK_KIND:
            ctx = ctx.with_flag(ContextFlag.ALWAYS)

        elif kind == ALWAYS_LATCH_BLOCK_KIND:
            ctx = ctx.with_flag(ContextFlag.ALWAYS_LATCH)

        # Computed once per block here rather than once per matching descendant node
        # in the rules themselves, which would re-walk the block's subtree O(K^2)
        # times. A deliberate exception to the usual layering
        # standard of not putting handler state behind a fact a rule could derive
        # statelessly -- here it can, but only cheaply if computed once per block.
        ctx = ctx.with_data("missing_sensitivity", missing_sensitivity_trigger_nodes(vnode.raw))
        ctx = ctx.with_data("mix_trigger", mixed_assignment_trigger_node(vnode.raw))

        return ctx

    def __str__(self) -> str:
        return "ProceduralBlockHandler"
