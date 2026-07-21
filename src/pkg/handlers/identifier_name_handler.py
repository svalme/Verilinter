from .base_handler import BaseHandler
from ..vnodes.base_vnode import BaseVNode
from ..vnodes.identifier_vnode import IdentifierNameVNode
from ..vnodes.vnode_factory import vnode_factory
from ..walk.dispatch import dispatch
from ..semantic.symbol import Symbol
from ..semantic.symbol_table import SymbolTable
from ..parser.syntax import enclosing_procedural_block, identifier_access_modes
from ..parser.types import IdentifierNameNode, IdentifierSelectNameNode
from ..walk.context import Context


@dispatch.register(IdentifierNameNode)
@dispatch.register(IdentifierSelectNameNode)
class IdentifierNameHandler(BaseHandler[IdentifierNameVNode]):

    def update_context(self, ctx: Context, vnode: IdentifierNameVNode, symbol_table: SymbolTable) -> Context:
        name = vnode.identifier_name
        if not name:
            return ctx.push(vnode)

        is_read, is_write = identifier_access_modes(ctx, vnode.raw)
        symbol = symbol_table.lookup_from_scope(name, ctx.scope())
        driver_block = enclosing_procedural_block(ctx) if is_write else None
        driver_id = None
        driver_location = None
        if driver_block is not None:
            loc = driver_block.location
            driver_id = (
                f"{driver_block.kind}:{loc.get('file', '')}:{loc['line']}:{loc['col']}"
            )
            driver_location = loc

        if symbol:
            symbol.add_use(
                vnode.location,
                read=is_read,
                write=is_write,
                driver_id=driver_id,
                driver_location=driver_location,
            )
        else:
            if symbol_table.current_file_uses_default_nettype_none():
                symbol = Symbol(name=name, kind="variable")
            else:
                symbol = Symbol(name=name, kind="implicit_net")
                symbol.is_implicit = True
            symbol.add_use(
                vnode.location,
                read=is_read,
                write=is_write,
                driver_id=driver_id,
                driver_location=driver_location,
            )
            ctx.scope().define(symbol)

        return ctx.push(vnode)

    def children(self, vnode: IdentifierNameVNode) -> list[BaseVNode]:
        return [vnode_factory.create(child, vnode.tree) for child in vnode.raw_children]

    def __str__(self) -> str:
        return "IdentifierNameHandler"
