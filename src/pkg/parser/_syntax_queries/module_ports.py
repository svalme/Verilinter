"""The ports of each module in a parsed file, read from the syntax alone."""
from __future__ import annotations

from typing import Iterator

from ..syntax_kinds import (
    COMPILATION_UNIT_KIND,
    HIERARCHY_INSTANTIATION_KIND,
    INTERFACE_PORT_HEADER_KIND,
    MODULE_DECLARATION_KIND,
    PORT_DECLARATION_KIND,
)
from ..traversal_guard import guarded_generator
from ..types import SyntaxTree
from .declarators import _ansi_port_list_items, _explicit_port_direction, _inherited_port_direction
from .module_file import module_declaration_name
from .instantiation import instantiation_type_name
from .shared import identifier_name, raw_node_children

_MAX_PORTS = 4096


def _declarator_names(raw: object) -> list[str]:
    """The names declared by a port node: one per declarator."""
    names: list[str] = []
    declarators = getattr(raw, "declarators", None)
    if declarators is None:
        declarator = getattr(raw, "declarator", None)
        declarators = [declarator] if declarator is not None else []
    for declarator in list(declarators)[:_MAX_PORTS]:
        name = identifier_name(getattr(declarator, "name", None)) or getattr(getattr(declarator, "name", None), "value", None)
        if isinstance(name, str) and name:
            names.append(name)
    return names


def module_port_directions(module: object) -> list[tuple[str, str | None]]:
    """`(name, direction)` of each port of a module declaration, in declaration order. The direction is None
    for a port with no direction keyword (an interface port)."""
    ports: list[tuple[str, str | None]] = []
    header_ports = getattr(getattr(module, "header", None), "ports", None)
    for item in _ansi_port_list_items(header_ports)[:_MAX_PORTS]:
        if getattr(getattr(item, "header", None), "kind", None) == INTERFACE_PORT_HEADER_KIND:
            direction = None
        else:
            direction = _explicit_port_direction(item) or _inherited_port_direction(item)
        ports.extend((name, direction) for name in _declarator_names(item))
    if ports:
        return ports
    for member in list(getattr(module, "members", None) or ())[:_MAX_PORTS]:
        if getattr(member, "kind", None) == PORT_DECLARATION_KIND:
            direction = _explicit_port_direction(member)
            ports.extend((name, direction) for name in _declarator_names(member))
    return ports


def module_ports_in_file(tree: SyntaxTree) -> dict[str, list[tuple[str, str | None]]]:
    """Module name to its ports for each module declared at the top level of the file."""
    root = tree.root
    found: dict[str, list[tuple[str, str | None]]] = {}
    if getattr(root, "kind", None) != COMPILATION_UNIT_KIND:
        return found
    for member in getattr(root, "members", None) or ():
        if getattr(member, "kind", None) != MODULE_DECLARATION_KIND:
            continue
        name = module_declaration_name(member)
        if name:
            found.setdefault(name, module_port_directions(member))
    return found


@guarded_generator(max_depth=128)
def _iter_instantiations(node: object) -> Iterator[object]:
    if getattr(node, "kind", None) == HIERARCHY_INSTANTIATION_KIND:
        yield node
    for child in raw_node_children(node):
        yield from _iter_instantiations(child)


def instantiated_module_names(tree: SyntaxTree) -> list[str]:
    """The sorted names of the modules a file instantiates, read from the syntax alone."""
    names = {instantiation_type_name(node) for node in _iter_instantiations(tree.root)}
    return sorted(name for name in names if name)
