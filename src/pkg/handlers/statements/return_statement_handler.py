from ...parser.syntax import return_statement_has_value
from ...parser.types import ReturnStatementNode
from ...semantic.scope import enclosing_function_scope
from ...semantic.symbol_table import SymbolTable
from ...vnodes.syntax_vnode import SyntaxVNode
from ...walk.context import Context
from ...walk.dispatch import dispatch
from ..syntax_node_handler import SyntaxNodeHandler


@dispatch.register(ReturnStatementNode)
class ReturnStatementHandler(SyntaxNodeHandler):
    """Counts `return expr;` as a write of the enclosing function's result variable.

    A function can export its value by assigning its own name or by returning it; both
    leave the result variable driven.
    """

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        if return_statement_has_value(vnode.raw):
            scope = enclosing_function_scope(ctx.scope())
            result = scope.function_result() if scope is not None else None
            if result is not None:
                result.add_use(vnode.location, write=True)
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "ReturnStatementHandler"
