from ..walk.dispatch import dispatch
from ..walk.context import Context
from ..parser.syntax import (
    declarator_bit_width,
    declarator_has_initializer,
    declarator_initializer_expression,
    declarator_initializer_value,
    declarator_is_event,
    declarator_is_enum_member,
    declarator_is_localparam,
    declarator_is_parameter,
    declarator_is_port,
    declarator_is_signed,
    declarator_name,
    declarator_packed_dimension_texts,
    declarator_packed_dimension_widths,
    declarator_packed_range,
    declarator_port_direction,
    declarator_unpacked_dimension_texts,
    declarator_unpacked_dimension_widths,
    enclosing_continuous_assign,
    enclosing_procedural_block,
    source_text_for_node,
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
        if declarator_is_enum_member(ctx):
            kind = "enum_member"
        elif declarator_is_parameter(ctx):
            kind = "parameter"
        elif ctx.scope().kind == "aggregate":
            kind = "field"
        else:
            kind = "variable"
        symbol = Symbol(name=name, kind=kind)
        if kind == "parameter":
            symbol.is_localparam = declarator_is_localparam(ctx)
        elif kind == "enum_member":
            symbol.is_constant = True
        symbol.is_port = declarator_is_port(ctx)
        if symbol.is_port:
            symbol.port_direction = declarator_port_direction(ctx)
        symbol.bit_width = declarator_bit_width(ctx)
        symbol.msb, symbol.lsb = declarator_packed_range(ctx)
        symbol.packed_dimensions = declarator_packed_dimension_texts(ctx, vnode.tree)
        symbol.packed_dimension_widths = declarator_packed_dimension_widths(ctx)
        symbol.unpacked_dimensions = declarator_unpacked_dimension_texts(vnode.raw, vnode.tree)
        symbol.unpacked_dimension_widths = declarator_unpacked_dimension_widths(vnode.raw, scope=ctx.scope())
        symbol.is_signed = declarator_is_signed(ctx)
        symbol.is_event = declarator_is_event(ctx)
        symbol.add_declaration(vnode.location)
        if declarator_has_initializer(vnode.raw):
            symbol.has_declaration_initializer = True
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
            init_expr = declarator_initializer_expression(vnode.raw)
            if init_expr is not None and symbol.initializer_text is None:
                symbol.initializer_text = source_text_for_node(init_expr, vnode.tree)
            if kind in ("parameter", "enum_member"):
                symbol.value = declarator_initializer_value(vnode.raw, scope=ctx.scope())
        ctx.scope().define(symbol)
        return ctx.push(vnode)

    def __str__(self) -> str:
        return "DeclaratorHandler"
