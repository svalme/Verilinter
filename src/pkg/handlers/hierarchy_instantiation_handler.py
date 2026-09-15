from ..walk.dispatch import dispatch
from ..walk.context import Context
from ..semantic.models import InstanceRecord, ParameterOverride, PortConnection
from ..semantic.scope import Scope, enclosing_module_scope
from ..semantic.symbol import Symbol
from ..semantic.symbol_table import SymbolTable
from ..parser.syntax import (
    branch_exclusivity_signature,
    hierarchical_instance_name,
    hierarchical_instance_list,
    instantiation_type_name,
    is_named_parameter_override,
    is_ordered_parameter_override,
    named_parameter_override_name,
    named_port_connection_name,
    node_location,
    parameter_override_list,
    port_connection_list,
    port_connection_expression,
    simple_identifier_text,
    simple_expression_width_and_signed,
    source_text_for_node,
)
from ..parser.types import HierarchicalInstanceNode, HierarchyInstantiationNode
from ..vnodes.syntax_vnode import SyntaxVNode
from .syntax_node_handler import SyntaxNodeHandler


@dispatch.register(HierarchyInstantiationNode)
class HierarchyInstantiationHandler(SyntaxNodeHandler):
    def update_context(self, ctx: Context, vnode: SyntaxVNode, symbol_table: SymbolTable) -> Context:
        type_name = instantiation_type_name(vnode.raw)
        enclosing_module = enclosing_module_scope(ctx.scope())
        if type_name:
            symbol_table.register_module_reference(type_name, vnode.location)

            if enclosing_module is not None and enclosing_module.name:
                symbol_table.register_instantiation_edge(enclosing_module.name, type_name, vnode.location)

        parameter_overrides: list[ParameterOverride] = []
        parameter_override_kinds: set[str] = set()
        for param in parameter_override_list(vnode.raw):
            if is_named_parameter_override(param):
                parameter_overrides.append(
                    ParameterOverride(
                        kind="named",
                        param_name=named_parameter_override_name(param),
                        location=node_location(param, vnode.tree),
                    )
                )
                parameter_override_kinds.add("named")
            elif is_ordered_parameter_override(param):
                parameter_overrides.append(
                    ParameterOverride(
                        kind="ordered",
                        location=node_location(param, vnode.tree),
                    )
                )
                parameter_override_kinds.add("ordered")
        parameter_override_style = (
            "mixed" if len(parameter_override_kinds) > 1 else next(iter(parameter_override_kinds), "none")
        )

        for item in hierarchical_instance_list(vnode.raw):
            if not isinstance(item, HierarchicalInstanceNode):
                continue

            inst_name = hierarchical_instance_name(item)
            if inst_name:
                sym = Symbol(name=inst_name, kind="instance")
                sym.add_declaration(vnode.location)
                ctx.scope().define(sym)

            connections: list[PortConnection] = []
            connection_kinds: set[str] = set()
            for conn in port_connection_list(item):
                kind_name = type(conn).__name__
                if kind_name == "NamedPortConnectionSyntax":
                    expr = port_connection_expression(conn)
                    expr_text = source_text_for_node(expr, vnode.tree) if expr is not None else None
                    expr_width, expr_signed = (
                        simple_expression_width_and_signed(ctx.scope(), expr, vnode.tree)
                        if expr is not None
                        else (None, None)
                    )
                    connections.append(
                        PortConnection(
                            kind="named",
                            port_name=named_port_connection_name(conn),
                            expr_text=expr_text,
                            expr_name=simple_identifier_text(expr_text),
                            expr_width=expr_width,
                            expr_signed=expr_signed,
                            location=node_location(conn, vnode.tree),
                        )
                    )
                    connection_kinds.add("named")
                elif kind_name == "OrderedPortConnectionSyntax":
                    expr = port_connection_expression(conn)
                    expr_text = source_text_for_node(expr, vnode.tree) if expr is not None else None
                    expr_width, expr_signed = (
                        simple_expression_width_and_signed(ctx.scope(), expr, vnode.tree)
                        if expr is not None
                        else (None, None)
                    )
                    connections.append(
                        PortConnection(
                            kind="ordered",
                            expr_text=expr_text,
                            expr_name=simple_identifier_text(expr_text),
                            expr_width=expr_width,
                            expr_signed=expr_signed,
                            location=node_location(conn, vnode.tree),
                        )
                    )
                    connection_kinds.add("ordered")
                elif kind_name == "WildcardPortConnectionSyntax":
                    connections.append(
                        PortConnection(
                            kind="wildcard",
                            location=node_location(conn, vnode.tree),
                        )
                    )
                    connection_kinds.add("wildcard")
                elif kind_name == "EmptyPortConnectionSyntax":
                    connections.append(
                        PortConnection(
                            kind="empty",
                            location=node_location(conn, vnode.tree),
                        )
                    )

            explicit_kinds = connection_kinds - {"wildcard"}
            if len(explicit_kinds) > 1:
                style = "mixed"
            elif explicit_kinds:
                style = next(iter(explicit_kinds))
            elif "wildcard" in connection_kinds:
                style = "wildcard"
            else:
                style = "empty"
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
