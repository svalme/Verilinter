# src/pkg/handlers/signal_event_expression_handler.py

from ..walk.dispatch import dispatch
from ..walk.context import Context, ContextFlag
from ..semantic.symbol_table import SymbolTable
from ..parser.syntax import is_negedge_event, is_posedge_event
from ..parser.types import SignalEventExpressionNode
from ..vnodes.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(SignalEventExpressionNode)
class SignalEventExpressionHandler(SyntaxNodeHandler):

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        ctx = ctx.push(vnode)

        if is_posedge_event(vnode.raw):
            ctx = ctx.with_flag(ContextFlag.POSEDGE)

        if is_negedge_event(vnode.raw):
            ctx = ctx.with_flag(ContextFlag.NEGEDGE)

        return ctx

    def __str__(self) -> str:
        return "SignalEventExpressionHandler"
