from .base_handler import BaseHandler
from ..vnodes.base_vnode import BaseVNode
from ..vnodes.identifier_vnode import IdentifierNameVNode
from ..vnodes.vnode_factory import vnode_factory
from ..walk.dispatch import dispatch
from ..semantic.symbol import Symbol
from ..semantic.symbol_table import SymbolTable
from ..parser.syntax import (
    enclosing_continuous_assign,
    enclosing_procedural_block,
    identifier_access_modes,
    is_bind_directive_target,
    is_combinational_driver_block,
    is_continuous_assign,
    is_cover_cross_item,
    is_defparam_target,
    is_disable_statement_target,
    is_extends_clause_base_name,
    is_invocation_callee,
    is_named_type_reference,
    is_subroutine_prototype_name,
    is_tristate_continuous_assign,
)
from ..parser.types import IDENTIFIER_NAME_NODE_TYPES
from ..walk.context import Context

# Every check here recognizes an IdentifierNameSyntax-shaped node that names a
# module/scope/type/label/callee/parameter-path rather than a variable being read
# or written. Each was found the same way: some rule/audit exercised a construct
# IdentifierNameHandler had never been taught about, and the identifier fell
# through to implicit-net creation. Add to this list rather than inlining another
# `or` clause in update_context -- it is expected to keep growing.
_STRUCTURAL_NAME_PREDICATES = (
    is_bind_directive_target,
    is_subroutine_prototype_name,
    is_defparam_target,
    is_disable_statement_target,
    is_named_type_reference,
    is_invocation_callee,
    is_cover_cross_item,
    is_extends_clause_base_name,
)


def _is_structural_name_reference(raw: object) -> bool:
    return any(predicate(raw) for predicate in _STRUCTURAL_NAME_PREDICATES)


class IdentifierNameHandler(BaseHandler[IdentifierNameVNode]):

    def update_context(self, ctx: Context, vnode: IdentifierNameVNode, symbol_table: SymbolTable) -> Context:
        name = vnode.identifier_name
        if not name or _is_structural_name_reference(vnode.raw):
            return ctx.push(vnode)

        is_read, is_write = identifier_access_modes(ctx, vnode.raw)
        symbol = symbol_table.lookup_from_scope(name, ctx.scope())
        # Computed for reads too (not just writes) so COMBINATIONAL_LOOP can group
        # every read/write in one combinational statement/block by driver_id. The
        # only existing consumer, NO_MULTIPLE_DRIVERS, already filters to
        # `event["write"]` before ever touching `driver_id`, so this is safe.
        driver_block = enclosing_procedural_block(ctx) or enclosing_continuous_assign(ctx)
        driver_id = None
        driver_location = None
        if driver_block is not None:
            loc = driver_block.location
            driver_id = (
                f"{driver_block.kind}:{loc.get('file', '')}:{loc['line']}:{loc['col']}"
            )
            driver_location = loc
            if is_write and is_combinational_driver_block(driver_block):
                symbol_table.mark_combinational_driver(driver_id)
            if is_write and is_continuous_assign(driver_block.raw) and is_tristate_continuous_assign(driver_block.raw):
                symbol_table.mark_tristate_driver(driver_id)

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


for _raw_type in IDENTIFIER_NAME_NODE_TYPES:
    dispatch.register(_raw_type)(IdentifierNameHandler)
