from __future__ import annotations

from typing import TYPE_CHECKING

from ..syntax_kinds import (
    ARGUMENT_LIST_KIND,
    ASCENDING_RANGE_SELECT_KIND,
    BIT_SELECT_KIND,
    DESCENDING_RANGE_SELECT_KIND,
    ELEMENT_SELECT_KIND,
    FUNCTION_DECLARATION_KIND,
    FUNCTION_PORT_KIND,
    INVOCATION_EXPRESSION_KIND,
    MODULE_DECLARATION_KIND,
    NAMED_ARGUMENT_KIND,
    ORDERED_ARGUMENT_KIND,
    PACKAGE_DECLARATION_KIND,
    PORT_DECLARATION_KIND,
    PORT_DIRECTION_TOKEN_KINDS,
    SCOPED_NAME_KIND,
    SIMPLE_RANGE_SELECT_KIND,
    SYSTEM_NAME_KIND,
    TASK_DECLARATION_KIND,
    VOID_TYPE_KIND,
)
from ..types import SyntaxNode
from .package_scoping import scoped_name_package_qualifier
from .shared import identifier_name

if TYPE_CHECKING:
    from ...semantic.symbol_table import SymbolTable
    from ...walk.context import Context

_SELECTOR_KINDS = (
    BIT_SELECT_KIND,
    SIMPLE_RANGE_SELECT_KIND,
    ASCENDING_RANGE_SELECT_KIND,
    DESCENDING_RANGE_SELECT_KIND,
    ELEMENT_SELECT_KIND,
)


def subroutine_name(raw: object) -> str | None:
    """Name of a function/task declaration, or None if it has no plain name."""
    return identifier_name(getattr(getattr(raw, "prototype", None), "name", None))


def function_returns_value(raw: object) -> bool:
    """True if `raw` is a function declaration with a non-`void` return type."""
    return_type = getattr(getattr(raw, "prototype", None), "returnType", None)
    if return_type is None:
        return True
    return getattr(return_type, "kind", None) != VOID_TYPE_KIND


def extract_formals_from_subroutine_syntax(node: object) -> list[tuple[str, str]]:
    """Extract (formal_name, direction) list from a TaskDeclaration or FunctionDeclaration node,
    preserving declaration order and inherited port directions."""
    result: list[tuple[str, str]] = []
    proto = getattr(node, "prototype", None)
    port_list = getattr(proto, "portList", None)
    ports = getattr(port_list, "ports", None)
    if ports is not None:
        direction = "input"
        for p in ports:
            if getattr(p, "kind", None) == FUNCTION_PORT_KIND:
                d_token = getattr(p, "direction", None)
                d_str = PORT_DIRECTION_TOKEN_KINDS.get(getattr(d_token, "kind", None))
                if d_str is not None:
                    direction = d_str
                decl = getattr(p, "declarator", None)
                name_token = getattr(decl, "name", None)
                name = identifier_name(name_token)
                if name:
                    result.append((name, direction))
    if result:
        return result

    # Non-ANSI task/function declarations specify port directions in body items
    for item in getattr(node, "items", ()) or ():
        if getattr(item, "kind", None) != PORT_DECLARATION_KIND:
            continue
        header = getattr(item, "header", None)
        d_token = getattr(header, "direction", None)
        direction = PORT_DIRECTION_TOKEN_KINDS.get(getattr(d_token, "kind", None), "input")
        for decl in getattr(item, "declarators", ()) or ():
            name = identifier_name(getattr(decl, "name", None))
            if name:
                result.append((name, direction))
    return result


def _find_subroutine_in_container_syntax(container: object, callee_name: str) -> object | None:
    for m in getattr(container, "members", ()):
        if getattr(m, "kind", None) in (TASK_DECLARATION_KIND, FUNCTION_DECLARATION_KIND):
            proto = getattr(m, "prototype", None)
            name = identifier_name(getattr(proto, "name", None))
            if name == callee_name:
                return m
    return None


def subroutine_formal_direction(
    raw: object, symbol_table: SymbolTable, ctx: Context
) -> str | None:
    """If `raw` is passed as an argument to a user-defined subroutine call (task or function),
    returns the direction of the corresponding formal argument ("output", "inout", "ref", "input").
    If `raw` is inside a selector expression (e.g. index `idx` in `arr[idx]`), returns "input".
    If `raw` is not a subroutine argument or the subroutine cannot be resolved, returns None.
    """
    if not isinstance(raw, SyntaxNode):
        return None

    node = raw
    parent = getattr(node, "parent", None)
    depth = 0
    while parent is not None and getattr(parent, "kind", None) not in (ORDERED_ARGUMENT_KIND, NAMED_ARGUMENT_KIND) and depth < 64:
        depth += 1
        node = parent
        parent = getattr(parent, "parent", None)
    if parent is None or depth >= 64:
        return None

    arg_node = parent
    arg_list = getattr(arg_node, "parent", None)
    if getattr(arg_list, "kind", None) != ARGUMENT_LIST_KIND:
        return None

    invocation = getattr(arg_list, "parent", None)
    if getattr(invocation, "kind", None) != INVOCATION_EXPRESSION_KIND:
        return None

    callee = getattr(invocation, "left", None)
    if callee is None or getattr(callee, "kind", None) == SYSTEM_NAME_KIND:
        return None

    # If raw is inside an index or range selector of the argument, it is an input index read
    check_node = raw
    check_depth = 0
    while check_node is not None and check_node is not arg_node and check_depth < 64:
        check_depth += 1
        p = getattr(check_node, "parent", None)
        if p is not None and getattr(p, "kind", None) in _SELECTOR_KINDS:
            return "input"
        check_node = p

    # Determine callee name and optional package qualifier
    package_qualifier: str | None = None
    callee_name: str | None
    if getattr(callee, "kind", None) == SCOPED_NAME_KIND:
        package_qualifier = scoped_name_package_qualifier(callee) or identifier_name(getattr(callee, "left", None))
        callee_name = identifier_name(getattr(callee, "right", None))
    else:
        callee_name = identifier_name(callee)

    if not callee_name:
        return None

    formals: list[tuple[str, str]] | None = None

    # 1. Resolve from SymbolTable scope hierarchy
    if package_qualifier is not None:
        pkg_scope = symbol_table.lookup_package(package_qualifier)
        if pkg_scope is not None:
            for child in pkg_scope.children:
                if child.kind in ("task", "function") and child.name == callee_name:
                    formals = [
                        (s.name, s.port_direction or "input")
                        for s in child.symbols.values()
                        if s.is_port and not getattr(s, "is_function_return", False) and s.name != child.name
                    ]
                    break
    else:
        # Search from current scope upwards (module, block, etc.)
        scope = getattr(ctx, "scope", lambda: None)()
        scope_depth = 0
        while scope is not None and formals is None and scope_depth < 64:
            scope_depth += 1
            for child in getattr(scope, "children", ()):
                if getattr(child, "kind", None) in ("task", "function") and getattr(child, "name", None) == callee_name:
                    formals = [
                        (s.name, s.port_direction or "input")
                        for s in getattr(child, "symbols", {}).values()
                        if getattr(s, "is_port", False)
                        and not getattr(s, "is_function_return", False)
                        and getattr(s, "name", None) != child.name
                    ]
                    break
            # Also check imported packages for this scope
            for pkg_name, imported_name in getattr(scope, "imports", ()):
                if imported_name is not None and imported_name != callee_name:
                    continue
                for pkg_scope in getattr(symbol_table, "packages", {}).get(pkg_name, ()):
                    for child in getattr(pkg_scope, "children", ()):
                        if getattr(child, "kind", None) in ("task", "function") and getattr(child, "name", None) == callee_name:
                            formals = [
                                (s.name, s.port_direction or "input")
                                for s in getattr(child, "symbols", {}).values()
                                if getattr(s, "is_port", False)
                                and not getattr(s, "is_function_return", False)
                                and getattr(s, "name", None) != child.name
                            ]
                            break
                    if formals is not None:
                        break
                if formals is not None:
                    break
            scope = getattr(scope, "parent", None)

    # 2. If not found in SymbolTable (e.g. forward-called subroutine declared later in source), query AST
    if formals is None:
        if package_qualifier is not None:
            # Look for package declaration in tree root
            root = invocation
            root_depth = 0
            while getattr(root, "parent", None) is not None and root_depth < 64:
                root_depth += 1
                root = root.parent
            for m in getattr(root, "members", ()):
                if getattr(m, "kind", None) == PACKAGE_DECLARATION_KIND:
                    header = getattr(m, "header", None)
                    pkg_name = identifier_name(getattr(header, "name", None))
                    if pkg_name == package_qualifier:
                        sub = _find_subroutine_in_container_syntax(m, callee_name)
                        if sub is not None:
                            formals = extract_formals_from_subroutine_syntax(sub)
                        break
        else:
            # Search in enclosing module/package members
            container = invocation
            container_depth = 0
            while container is not None and getattr(container, "kind", None) not in (
                MODULE_DECLARATION_KIND,
                PACKAGE_DECLARATION_KIND,
            ) and container_depth < 64:
                container_depth += 1
                container = getattr(container, "parent", None)
            if container is not None:
                sub = _find_subroutine_in_container_syntax(container, callee_name)
                if sub is not None:
                    formals = extract_formals_from_subroutine_syntax(sub)

            # Also check imported packages declared in this syntax tree
            if formals is None:
                scope = getattr(ctx, "scope", lambda: None)()
                scope_depth = 0
                while scope is not None and formals is None and scope_depth < 64:
                    scope_depth += 1
                    for pkg_name, imported_name in getattr(scope, "imports", ()):
                        if imported_name is not None and imported_name != callee_name:
                            continue
                        root = invocation
                        root_depth = 0
                        while getattr(root, "parent", None) is not None and root_depth < 64:
                            root_depth += 1
                            root = root.parent
                        for m in getattr(root, "members", ()):
                            if getattr(m, "kind", None) == PACKAGE_DECLARATION_KIND:
                                header = getattr(m, "header", None)
                                p_name = identifier_name(getattr(header, "name", None))
                                if p_name == pkg_name:
                                    sub = _find_subroutine_in_container_syntax(m, callee_name)
                                    if sub is not None:
                                        formals = extract_formals_from_subroutine_syntax(sub)
                                        break
                        if formals is not None:
                            break
                    scope = getattr(scope, "parent", None)

    if not formals:
        return None

    # Match argument position or name to formal direction
    if getattr(arg_node, "kind", None) == ORDERED_ARGUMENT_KIND:
        ordered_args = [a for a in getattr(arg_list, "parameters", ()) if getattr(a, "kind", None) == ORDERED_ARGUMENT_KIND]
        if arg_node in ordered_args:
            idx = ordered_args.index(arg_node)
            if idx < len(formals):
                return formals[idx][1]
    elif getattr(arg_node, "kind", None) == NAMED_ARGUMENT_KIND:
        arg_name = identifier_name(getattr(arg_node, "name", None))
        for f_name, f_dir in formals:
            if f_name == arg_name:
                return f_dir

    return None
