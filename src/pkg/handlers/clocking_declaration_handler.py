from __future__ import annotations

from ..parser.syntax import clocking_declaration_signals
from ..parser.types import ClockingDeclarationNode
from ..semantic.symbol import Symbol
from ..semantic.symbol_table import SymbolTable
from ..vnodes.base_vnode import BaseVNode
from ..vnodes.syntax_vnode import SyntaxVNode
from ..vnodes.vnode_factory import vnode_factory
from ..walk.context import Context
from ..walk.dispatch import dispatch
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(ClockingDeclarationNode)
class ClockingDeclarationHandler(SyntaxNodeHandler):
    """Handles ClockingDeclarationSyntax by registering clocking signal use-events (reads and writes)
    into the active module scope's symbol table with driver IDs representing the clocking block."""

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        clocking_loc = vnode.location
        driver_id = f"clocking:{clocking_loc.get('file', '')}:{clocking_loc['line']}:{clocking_loc['col']}"

        scope = ctx.scope()
        signals = clocking_declaration_signals(vnode.raw, vnode.tree)
        for name, is_input, is_output, loc in signals:
            lookup = getattr(scope, "lookup_hierarchical", None)
            symbol = lookup(name) if callable(lookup) else getattr(scope, "lookup", lambda _n: None)(name)
            if symbol is None:
                symbol = Symbol(name=name, kind="variable")
                scope.add_symbol(symbol)

            if is_output:
                symbol.add_use(
                    loc,
                    read=False,
                    write=True,
                    driver_id=driver_id,
                    driver_location=clocking_loc,
                )
            if is_input:
                symbol.add_use(
                    loc,
                    read=True,
                    write=False,
                )

        return ctx.push(vnode)

    def children(self, vnode: SyntaxVNode) -> list[BaseVNode]:
        event_node = getattr(vnode.raw, "event", None)
        if event_node is not None:
            return [vnode_factory.create(event_node, vnode.tree)]
        return []
