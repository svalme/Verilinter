"""Module-instantiation shape queries: instance/type names, port connections,
and parameter overrides (named and ordered)."""

from ..syntax_kinds import (
    NAMED_PARAM_ASSIGNMENT_KIND,
    NAMED_PORT_CONNECTION_KIND,
    ORDERED_PARAM_ASSIGNMENT_KIND,
    ORDERED_PORT_CONNECTION_KIND,
    WILDCARD_PORT_CONNECTION_KIND,
)
from ..types import SyntaxNode


def instantiation_type_name(raw: object) -> str | None:
    type_node = getattr(raw, "type", None)
    value = getattr(type_node, "value", None)
    return value if isinstance(value, str) and value else None


def hierarchical_instance_name(raw: object) -> str | None:
    decl = getattr(raw, "decl", None)
    name = getattr(decl, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def hierarchical_instance_list(raw: object) -> list[SyntaxNode]:
    """Return the instance nodes under a `HierarchyInstantiationSyntax`, or `[]`
    if the node has no recognizable instance list."""
    items = getattr(raw, "instances", None)
    if items is None:
        return []
    return [item for item in items if isinstance(item, SyntaxNode)]


def named_port_connection_name(raw: object) -> str | None:
    name = getattr(raw, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None


def port_connection_expression(raw: object) -> SyntaxNode | None:
    expr = getattr(raw, "expr", None)
    return expr if isinstance(expr, SyntaxNode) else None


def parameter_override_list(raw: object) -> list[SyntaxNode]:
    """Return the individual parameter-override syntax nodes from a
    `HierarchyInstantiationSyntax.parameters` field (`#(...)`), or `[]` if the
    instantiation has no parameter override list at all."""
    param_assignment = getattr(raw, "parameters", None)
    if param_assignment is None:
        return []
    items = getattr(param_assignment, "parameters", None)
    if items is None:
        return []
    return [item for item in items if isinstance(item, SyntaxNode)]


def port_connection_list(raw: object) -> list[SyntaxNode]:
    """Return the per-port connection nodes from a
    `HierarchicalInstanceSyntax.connections` field, or `[]` when absent."""
    items = getattr(raw, "connections", None)
    if items is None:
        return []
    return [item for item in items if isinstance(item, SyntaxNode)]


def is_port_connection_node(raw: object) -> bool:
    """True for a `NamedPortConnectionSyntax`/`OrderedPortConnectionSyntax`
    node -- one entry of a `HierarchicalInstanceSyntax.connections` list (see
    `port_connection_list`). Used by `enclosing_port_connection` to tell an
    identifier used to wire a net into an instance port apart from an
    ordinary read/write, since the connected port's direction (which side is
    actually driving the net) generally isn't resolvable at the point a
    single file is walked -- the instantiated module may be defined in
    another file, or simply not yet visited."""
    return getattr(raw, "kind", None) in (
        NAMED_PORT_CONNECTION_KIND,
        ORDERED_PORT_CONNECTION_KIND,
    )


def is_named_port_connection(raw: object) -> bool:
    return getattr(raw, "kind", None) == NAMED_PORT_CONNECTION_KIND


def is_ordered_port_connection(raw: object) -> bool:
    return getattr(raw, "kind", None) == ORDERED_PORT_CONNECTION_KIND


def is_wildcard_port_connection(raw: object) -> bool:
    return getattr(raw, "kind", None) == WILDCARD_PORT_CONNECTION_KIND


def is_named_parameter_override(raw: object) -> bool:
    return getattr(raw, "kind", None) == NAMED_PARAM_ASSIGNMENT_KIND


def is_ordered_parameter_override(raw: object) -> bool:
    return getattr(raw, "kind", None) == ORDERED_PARAM_ASSIGNMENT_KIND


def named_parameter_override_name(raw: object) -> str | None:
    name = getattr(raw, "name", None)
    value = getattr(name, "value", None)
    return value if isinstance(value, str) and value else None
