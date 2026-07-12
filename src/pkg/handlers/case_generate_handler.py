from ..walk.dispatch import dispatch
from ..walk.context import Context, ContextFlag
from ..semantic.symbol_table import SymbolTable
from ..parser.syntax import has_default_case_item, is_case_generate_keyword_pair
from ..parser.types import CaseGenerateNode
from ..vnodes.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(CaseGenerateNode)
class CaseGenerateHandler(SyntaxNodeHandler):

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        ctx = ctx.push(vnode)

        if is_case_generate_keyword_pair(vnode.raw):
            ctx = ctx.with_flag(ContextFlag.CASE_GENERATE)
            if has_default_case_item(vnode.raw):
                ctx = ctx.with_flag(ContextFlag.DEFAULT)

        return ctx

    def __str__(self) -> str:
        return "CaseGenerateHandler"
