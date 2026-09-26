from __future__ import annotations

from typing import TYPE_CHECKING

from ..walk.dispatch import dispatch
from ..walk.context import Context
from ..semantic.models import InstanceRecord
from ..semantic.scope import Scope, enclosing_module_scope
from ..semantic.symbol import Symbol
from ..semantic.symbol_table import SymbolTable
from ..parser.syntax import (
    branch_exclusivity_signature,
    hierarchical_instance_name,
    hierarchical_instance_list,
    instantiation_type_name,
)
from ..parser.types import HierarchicalInstanceNode, HierarchyInstantiationNode
from ..vnodes.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler
from .hierarchy_instantiation import (
    ParameterOverrideExtractor,
    PortConnectionExtractor,
)


@dispatch.register(HierarchyInstantiationNode)
class HierarchyInstantiationHandler(SyntaxNodeHandler):
    """Handles hierarchy instantiation syntax nodes, coordinating parameter

    override extraction, port connection parsing, and instance registration.
    """

    def __init__(
        self,
        parameter_extractor: ParameterOverrideExtractor | None = None,
        connection_extractor: PortConnectionExtractor | None = None,
    ) -> None:
        self.parameter_extractor = (
            parameter_extractor if parameter_extractor is not None else ParameterOverrideExtractor()
        )
        self.connection_extractor = (
            connection_extractor if connection_extractor is not None else PortConnectionExtractor()
        )

    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        type_name = instantiation_type_name(vnode.raw)
        enclosing_module = enclosing_module_scope(ctx.scope())
        if type_name:
            symbol_table.register_module_reference(type_name, vnode.location)

            if enclosing_module is not None and enclosing_module.name:
                symbol_table.register_instantiation_edge(enclosing_module.name, type_name, vnode.location)

        parameter_overrides, parameter_override_style = self.parameter_extractor.extract(
            vnode.raw, vnode.tree, ctx.scope()
        )

        for item in hierarchical_instance_list(vnode.raw):
            if not isinstance(item, HierarchicalInstanceNode):
                continue

            inst_name = hierarchical_instance_name(item)
            if inst_name:
                sym = Symbol(name=inst_name, kind="instance")
                sym.add_declaration(vnode.location)
                ctx.scope().define(sym)

            connections, style = self.connection_extractor.extract(
                item, vnode.tree, ctx.scope()
            )

            for conn in connections:
                if getattr(conn, "is_shorthand", False) and conn.port_name:
                    sym = symbol_table.lookup_from_scope(conn.port_name, ctx.scope())
                    if sym is not None:
                        sym.add_use(conn.location, read=True, in_port_connection=True)

            symbol_table.register_instantiation(
                InstanceRecord(
                    parent_module=enclosing_module.name if enclosing_module is not None else None,
                    child_module=type_name,
                    instance_name=inst_name,
                    location=vnode.location,
                    connection_style=style,
                    connections=connections,
                    parameter_override_style=parameter_override_style,
                    parameter_overrides=parameter_overrides,
                    # Lets a driver-conflict rule recognize an instance instantiated
                    # in a `generate if`/`else` branch mutually exclusive with
                    # another driver of the same signal (see
                    # branch_exclusivity_signature) as not a real simultaneous
                    # conflict.
                    generate_branch_signature=branch_exclusivity_signature(vnode.raw, vnode.tree),
                )
            )

        return ctx.push(vnode)

    def __str__(self) -> str:
        return "HierarchyInstantiationHandler"
