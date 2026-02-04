import pyslang as sl
from ..ast.dispatch import dispatch
from ..ast.context import Context, ContextFlag
from ..ast.symbol_table import SymbolTable
from ..vnode.syntax_vnode import SyntaxVNode
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