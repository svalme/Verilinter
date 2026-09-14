from ..walk.dispatch import dispatch
from ..walk.context import Context
from ..parser.syntax import (
    declarator_bit_width,
    declarator_has_initializer,
    declarator_initializer_value,
    declarator_is_parameter,
    declarator_is_port,
    declarator_is_signed,
    declarator_name,
    declarator_port_direction,
    enclosing_continuous_assign,
    enclosing_procedural_block,
)
from ..semantic.symbol import Symbol
from ..semantic.symbol_table import SymbolTable
from ..parser.types import DeclaratorNode
from ..vnodes.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(DeclaratorNode)
class DeclaratorHandler(SyntaxNodeHandler):
    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        name = declarator_name(vnode.raw)
        if not name:
            return ctx.push(vnode)
        kind = "parameter" if declarator_is_parameter(ctx) else "variable"
        if ctx.scope().kind == "aggregate":
            kind = "field"
        symbol = Symbol(name=name, kind=kind)
        symbol.is_port = declarator_is_port(ctx)
        if symbol.is_port:
            symbol.port_direction = declarator_port_direction(ctx)
        symbol.bit_width = declarator_bit_width(ctx)
        symbol.is_signed = declarator_is_signed(ctx)
        symbol.add_declaration(vnode.location)
        if declarator_has_initializer(vnode.raw):
            # Compute driver_id the same way IdentifierNameHandler does for every
            # other write in this block -- otherwise this initializer write has
            # driver_id=None and READ_BEFORE_WRITE's seen_blocking_write_by_driver
            # scan never counts it, so a loop header's own condition read (e.g.
            # `for (int i = 0; i < N; i++)`) false-flags as reading before a write.
            driver_block = enclosing_procedural_block(ctx) or enclosing_continuous_assign(ctx)
            driver_id = None
            driver_location = None
            if driver_block is not None:
                loc = driver_block.location
                driver_id = (
                    f"{driver_block.kind}:{loc.get('file', '')}:{loc['line']}:{loc['col']}"
                )
                driver_location = loc
            symbol.add_use(
                vnode.location,
                write=True,
                driver_id=driver_id,
                driver_location=driver_location,
            )
            if kind == "parameter":
                symbol.value = declarator_initializer_value(vnode.raw)
        ctx.scope().define(symbol)
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "DeclaratorHandler"
