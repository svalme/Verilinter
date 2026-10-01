from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from ...parser.syntax import (
    named_port_connection_has_parentheses,
    named_port_connection_name,
    node_location,
    port_connection_expression,
    port_connection_list,
    simple_expression_width_and_signed,
    simple_identifier_text,
    source_text_for_node,
)
from ...parser.syntax_kinds import (
    EMPTY_PORT_CONNECTION_KIND,
    NAMED_PORT_CONNECTION_KIND,
    ORDERED_PORT_CONNECTION_KIND,
    WILDCARD_PORT_CONNECTION_KIND,
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
            conn_kind = getattr(conn, "kind", None)
            if conn_kind == NAMED_PORT_CONNECTION_KIND:
                port_name = named_port_connection_name(conn)
                expr = port_connection_expression(conn)
                has_open_paren = named_port_connection_has_parentheses(conn)
                is_shorthand = expr is None and not has_open_paren
                if expr is not None:
                    expr_text = source_text_for_node(expr, tree)
                    expr_name = simple_identifier_text(expr_text)
                    expr_width, expr_signed = self.width_resolver(scope, expr, tree)
                elif is_shorthand:
                    expr_text = port_name
                    expr_name = port_name
                    sym = scope.lookup(port_name) if scope is not None and port_name is not None else None
                    if sym is not None:
                        expr_width, expr_signed = sym.bit_width, sym.is_signed
                    else:
                        expr_width, expr_signed = None, None
                else:
                    expr_text = None
                    expr_name = None
                    expr_width, expr_signed = None, None
                connections.append(
                    PortConnection(
                        kind="named",
                        port_name=port_name,
                        expr_text=expr_text,
                        expr_name=expr_name,
                        expr_width=expr_width,
                        expr_signed=expr_signed,
                        location=node_location(conn, tree),
                        is_shorthand=is_shorthand,
                    )
                )
                connection_kinds.add("named")
            elif conn_kind == ORDERED_PORT_CONNECTION_KIND:
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
            elif conn_kind == WILDCARD_PORT_CONNECTION_KIND:
                connections.append(
                    PortConnection(
                        kind="wildcard",
                        location=node_location(conn, tree),
                    )
                )
                connection_kinds.add("wildcard")
            elif conn_kind == EMPTY_PORT_CONNECTION_KIND:
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
