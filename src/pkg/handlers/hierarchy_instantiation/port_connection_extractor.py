from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from ...parser.syntax import (
    named_port_connection_name,
    node_location,
    port_connection_expression,
    port_connection_list,
    simple_expression_width_and_signed,
    simple_identifier_text,
    source_text_for_node,
)
from ...semantic.models import PortConnection

if TYPE_CHECKING:
    from ...semantic.scope import Scope


class PortConnectionExtractor:
    """Extracts typed port connection records and connection style from an instance item."""

    def __init__(
        self,
        width_resolver: Callable[..., tuple[int | None, bool | None]] | None = None,
    ) -> None:
        self.width_resolver = (
            width_resolver if width_resolver is not None else simple_expression_width_and_signed
        )

    def extract(
        self,
        item: Any,
        tree: Any,
        scope: Scope | None = None,
    ) -> tuple[list[PortConnection], str]:
        connections: list[PortConnection] = []
        connection_kinds: set[str] = set()

        for conn in port_connection_list(item):
            kind_name = type(conn).__name__
            if kind_name == "NamedPortConnectionSyntax":
                expr = port_connection_expression(conn)
                expr_text = source_text_for_node(expr, tree) if expr is not None else None
                expr_width, expr_signed = (
                    self.width_resolver(scope, expr, tree)
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
                        location=node_location(conn, tree),
                    )
                )
                connection_kinds.add("named")
            elif kind_name == "OrderedPortConnectionSyntax":
                expr = port_connection_expression(conn)
                expr_text = source_text_for_node(expr, tree) if expr is not None else None
                expr_width, expr_signed = (
                    self.width_resolver(scope, expr, tree)
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
                        location=node_location(conn, tree),
                    )
                )
                connection_kinds.add("ordered")
            elif kind_name == "WildcardPortConnectionSyntax":
                connections.append(
                    PortConnection(
                        kind="wildcard",
                        location=node_location(conn, tree),
                    )
                )
                connection_kinds.add("wildcard")
            elif kind_name == "EmptyPortConnectionSyntax":
                connections.append(
                    PortConnection(
                        kind="empty",
                        location=node_location(conn, tree),
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

        return connections, style
