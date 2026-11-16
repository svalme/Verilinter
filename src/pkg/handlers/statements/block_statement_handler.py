"""A begin-end or fork-join block that declares a variable is its own namespace."""
from ...parser.syntax import block_declares_names
from ...parser.types import BlockStatementNode
from ...semantic.scope_kinds import ScopeKind
from ...walk.dispatch import dispatch
from ..syntax_node_handler import SyntaxNodeHandler


@dispatch.register(BlockStatementNode)
class BlockStatementHandler(SyntaxNodeHandler):
    """Gives a block with local declarations its own scope.

    `automatic int idx;` inside `always_comb begin : a ... end` and again inside `begin : b ... end` names two
    variables. A block with no declaration opens no scope, so most blocks cost nothing."""

    def update_context(self, ctx, vnode, symbol_table):
        if not block_declares_names(vnode.raw):
            return ctx.push(vnode)
        scope = symbol_table.new_scope(kind=ScopeKind.BLOCK, location=vnode.location)
        return ctx.push(vnode).with_scope(scope)

    def on_exit(self, ctx, vnode, symbol_table):
        if block_declares_names(vnode.raw):
            symbol_table.pop_scope()

    def __str__(self) -> str:
        return "BlockStatementHandler"
