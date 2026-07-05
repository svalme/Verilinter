import pyslang as sl
from ..walk.dispatch import dispatch
from ..walk.context import Context, ContextFlag
from ..semantic.symbol_table import SymbolTable
from ..vnodes.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(sl.CaseGenerateSyntax)
class CaseGenerateHandler(SyntaxNodeHandler):

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        ctx = ctx.push(vnode)

        if str(vnode.raw.keyword).strip() == "case" and str(vnode.raw.endCase).strip() == "endcase": 
            ctx = ctx.with_flag(ContextFlag.CASE_GENERATE)

        return ctx

    def __str__(self) -> str:
        return "CaseGenerateHandler"