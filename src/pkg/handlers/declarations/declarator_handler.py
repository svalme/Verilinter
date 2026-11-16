from ...walk.dispatch import dispatch
from ...walk.context import Context
from ...parser.syntax import (
    declarator_bit_width,
    declarator_has_initializer,
    declarator_interface_type_name,
    declarator_named_type_dimension_count,
    declarator_named_type_dimensions_width,
    declarator_named_type_reference,
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
from ...semantic.symbol import Symbol
from ...semantic.symbol_kind import SymbolKind
from ...semantic.symbol_table import SymbolTable
from ...parser.types import DeclaratorNode
from ...vnodes.syntax_vnode import SyntaxVNode
from ..syntax_node_handler import SyntaxNodeHandler
from ...semantic.scope_kinds import ScopeKind


@dispatch.register(DeclaratorNode)
class DeclaratorHandler(SyntaxNodeHandler):
    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        name = declarator_name(vnode.raw)
        if not name:
            return ctx.push(vnode)
        if declarator_is_enum_member(ctx):
            kind = SymbolKind.ENUM_MEMBER
        elif declarator_is_parameter(ctx):
            kind = SymbolKind.PARAMETER
        elif ctx.scope().kind == ScopeKind.AGGREGATE:
            kind = SymbolKind.FIELD
        else:
            kind = SymbolKind.VARIABLE
        symbol = Symbol(name=name, kind=kind)
        if kind is SymbolKind.PARAMETER:
            symbol.is_localparam = declarator_is_localparam(ctx)
        elif kind is SymbolKind.ENUM_MEMBER:
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
        symbol.interface_type_name = declarator_interface_type_name(ctx)
        symbol.named_type_dimension_count = declarator_named_type_dimension_count(ctx)
        if kind in (SymbolKind.VARIABLE, SymbolKind.FIELD) and symbol.bit_width is None:
            self._inherit_named_type(symbol, ctx)
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
            if kind.is_compile_time_constant:
                symbol.value = declarator_initializer_value(vnode.raw, scope=ctx.scope())
        ctx.scope().define(symbol)
        return ctx.push(vnode)

    @staticmethod
    def _inherit_named_type(symbol: Symbol, ctx: Context) -> None:
        """A variable declared with a typedef name takes the typedef's width, signedness and member widths;
        packed dimensions written after the type name multiply the width."""
        reference = declarator_named_type_reference(ctx)
        if reference is None:
            return
        package, type_name = reference
        scope = ctx.scope()
        typedef = scope.lookup_package_member(package, type_name) if package else scope.lookup_hierarchical(type_name)
        if typedef is None or typedef.kind is not SymbolKind.TYPEDEF or not isinstance(typedef.bit_width, int):
            return
        extra = declarator_named_type_dimensions_width(ctx)
        if extra is None:
            return
        symbol.bit_width = typedef.bit_width * extra
        if symbol.is_signed is None:
            symbol.is_signed = typedef.is_signed
        symbol.member_widths = typedef.member_widths

    def __str__(self) -> str:
        return "DeclaratorHandler"
