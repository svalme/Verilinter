import pyslang as sl
from ..ast.dispatch import dispatch
from ..ast.context import Context, ContextFlag
from ..vnode.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(sl.SignalEventExpressionSyntax)
class SignalEventExpressionHandler(SyntaxNodeHandler):

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table=None) -> Context:
        ctx = ctx.push(vnode)

        if str(vnode.raw.edge) == "posedge":
            ctx = ctx.with_flag(ContextFlag.POSEDGE)

        if str(vnode.raw.edge) == "negedge":
            ctx = ctx.with_flag(ContextFlag.NEGEDGE)

        return ctx

    def __str__(self) -> str:
        return "SignalEventExpressionHandler"