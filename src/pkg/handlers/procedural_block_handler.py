from ..walk.context import Context, ContextFlag
from ..semantic.symbol_table import SymbolTable
from .syntax_node_handler import SyntaxNodeHandler
from ..vnodes.syntax_vnode import SyntaxVNode

from ..parser.syntax import (
    ALWAYS_BLOCK_KIND,
    ALWAYS_COMB_BLOCK_KIND,
    ALWAYS_LATCH_BLOCK_KIND,
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

        return ctx

    def __str__(self) -> str:
        return "ProceduralBlockHandler"
