from ..vnode.base_vnode import BaseVNode
from ..ast.context import Context, ContextFlag
from ..ast.symbol_table import SymbolTable
from .syntax_node_handler import SyntaxNodeHandler
from ..vnode.syntax_vnode import SyntaxVNode

import pyslang as sl
from ..ast.dispatch import dispatch

@dispatch.register(sl.ProceduralBlockSyntax)
class ProceduralBlockHandler(SyntaxNodeHandler):

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        ctx = ctx.push(vnode)
        kind = vnode.kind

        if kind == sl.SyntaxKind.AlwaysCombBlock:
            ctx = ctx.with_flag(ContextFlag.ALWAYS_COMB)

        elif kind == sl.SyntaxKind.AlwaysBlock:
            ctx = ctx.with_flag(ContextFlag.ALWAYS)

        elif kind == sl.SyntaxKind.AlwaysLatchBlock:
            ctx = ctx.with_flag(ContextFlag.ALWAYS_LATCH)

        return ctx

    def __str__(self) -> str:
        return "ProceduralBlockHandler"