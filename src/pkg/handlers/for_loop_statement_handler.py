from ..walk.dispatch import dispatch
from ..walk.context import Context
from ..semantic.symbol_table import SymbolTable
from ..vnodes.syntax_vnode import SyntaxVNode
from ..parser.types import ForLoopStatementNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(ForLoopStatementNode)
class ForLoopStatementHandler(SyntaxNodeHandler):
    """Gives a procedural `for` loop's header (and body) its own nested scope.

    An inline-declared loop variable (`for (int i = 0; ...)`) is scoped to
    the loop itself by SystemVerilog's own rules, so the same name reused
    across two independent loops in the same module is ordinary, not a
    REDECLARED_VARIABLE collision. Without a dedicated scope here, the loop
    variable's DeclaratorNode defines it into the flat enclosing scope, where
    a second loop's identically-named variable collides with the first (a
    common idiom, e.g. a loop variable named `i`).
    """

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        scope = symbol_table.new_scope(kind="for", location=vnode.location)
        return ctx.push(vnode).with_scope(scope)

    def on_exit(self, _ctx: Context, _vnode: SyntaxVNode, symbol_table: SymbolTable) -> None:
        symbol_table.pop_scope()

    def __str__(self) -> str:
        return "ForLoopStatementHandler"
