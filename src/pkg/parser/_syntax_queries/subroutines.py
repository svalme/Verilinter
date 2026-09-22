from __future__ import annotations

from typing import TYPE_CHECKING
import pyslang as sl

from ..syntax_kinds import INVOCATION_EXPRESSION_KIND
from .package_scoping import scoped_name_package_qualifier
from .shared import identifier_name

if TYPE_CHECKING:
    from ...semantic.symbol_table import SymbolTable
    from ...walk.context import Context

_SELECTOR_KINDS = (
    sl.SyntaxKind.BitSelect,
    sl.SyntaxKind.SimpleRangeSelect,
    sl.SyntaxKind.AscendingRangeSelect,
    sl.SyntaxKind.DescendingRangeSelect,
    sl.SyntaxKind.ElementSelect,
)


def extract_formals_from_subroutine_syntax(node: object) -> list[tuple[str, str]]:
    """Extract (formal_name, direction) list from a TaskDeclaration or FunctionDeclaration node,
    preserving declaration order and inherited port directions."""
    proto = getattr(node, "prototype", None)
    if proto is None:
        return []
    port_list = getattr(proto, "portList", None)
    if port_list is None:
        return []
    ports = getattr(port_list, "ports", None)
    if ports is None:
        return []

    result: list[tuple[str, str]] = []
    direction = "input"
    for p in ports:
        if isinstance(p, sl.SyntaxNode) and type(p).__name__ == "FunctionPortSyntax":
            d_token = getattr(p, "direction", None)
            d_str = str(d_token).strip() if d_token is not None else ""
            if d_str in ("input", "output", "inout", "ref"):
                direction = d_str
            decl = getattr(p, "declarator", None)
            name_token = getattr(decl, "name", None)
            name = str(getattr(name_token, "value", "") or name_token).strip()
            result.append((name, direction))
    return result


def _find_subroutine_in_container_syntax(container: object, callee_name: str) -> object | None:
    for m in getattr(container, "members", ()):
        if getattr(m, "kind", None) in (sl.SyntaxKind.TaskDeclaration, sl.SyntaxKind.FunctionDeclaration):
            proto = getattr(m, "prototype", None)
            name = identifier_name(getattr(proto, "name", None)) or str(getattr(proto, "name", "")).strip()
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
    node = raw
    parent = getattr(node, "parent", None)
    while parent is not None and type(parent).__name__ not in ("OrderedArgumentSyntax", "NamedArgumentSyntax"):
        node = parent
        parent = getattr(parent, "parent", None)
    if parent is None:
        return None

    arg_node = parent
    arg_list = getattr(arg_node, "parent", None)
    if type(arg_list).__name__ != "ArgumentListSyntax":
        return None

    invocation = getattr(arg_list, "parent", None)
    if getattr(invocation, "kind", None) != INVOCATION_EXPRESSION_KIND:
        return None

    callee = getattr(invocation, "left", None)
    if callee is None or getattr(callee, "kind", None) == sl.SyntaxKind.SystemName:
        return None

    # If raw is inside an index or range selector of the argument, it is an input index read
    check_node = raw
    while check_node is not None and check_node is not arg_node:
        p = getattr(check_node, "parent", None)
        if p is not None and getattr(p, "kind", None) in _SELECTOR_KINDS:
            return "input"
        check_node = p

    # Determine callee name and optional package qualifier
    package_qualifier: str | None = None
    callee_name: str
    if getattr(callee, "kind", None) == sl.SyntaxKind.ScopedName:
        package_qualifier = scoped_name_package_qualifier(callee) or identifier_name(getattr(callee, "left", None))
        callee_name = identifier_name(getattr(callee, "right", None)) or str(callee.right).strip()
    else:
        callee_name = identifier_name(callee) or str(callee).strip()

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
                        if s.is_port and s.name != child.name
                    ]
                    break
    else:
        # Search from current scope upwards (module, block, etc.)
        scope = ctx.scope()
        while scope is not None and formals is None:
            for child in scope.children:
                if child.kind in ("task", "function") and child.name == callee_name:
                    formals = [
                        (s.name, s.port_direction or "input")
                        for s in child.symbols.values()
                        if s.is_port and s.name != child.name
                    ]
                    break
            # Also check imported packages for this scope
            for pkg_name, imported_name in scope.imports:
                if imported_name is not None and imported_name != callee_name:
                    continue
                for pkg_scope in symbol_table.packages.get(pkg_name, ()):
                    for child in pkg_scope.children:
                        if child.kind in ("task", "function") and child.name == callee_name:
                            formals = [
                                (s.name, s.port_direction or "input")
                                for s in child.symbols.values()
                                if s.is_port and s.name != child.name
                            ]
                            break
                    if formals is not None:
                        break
                if formals is not None:
                    break
            scope = scope.parent

    # 2. If not found in SymbolTable (e.g. forward-called subroutine declared later in source), query AST
    if formals is None:
        if package_qualifier is not None:
            # Look for package declaration in tree root
            root = invocation
            while getattr(root, "parent", None) is not None:
                root = root.parent
            for m in getattr(root, "members", ()):
                if getattr(m, "kind", None) == sl.SyntaxKind.PackageDeclaration:
                    pkg_name = identifier_name(getattr(m.header, "name", None)) or str(m.header.name).strip()
                    if pkg_name == package_qualifier:
                        sub = _find_subroutine_in_container_syntax(m, callee_name)
                        if sub is not None:
                            formals = extract_formals_from_subroutine_syntax(sub)
                        break
        else:
            # Search in enclosing module/package members
            container = invocation
            while container is not None and getattr(container, "kind", None) not in (
                sl.SyntaxKind.ModuleDeclaration,
                sl.SyntaxKind.PackageDeclaration,
            ):
                container = getattr(container, "parent", None)
            if container is not None:
                sub = _find_subroutine_in_container_syntax(container, callee_name)
                if sub is not None:
                    formals = extract_formals_from_subroutine_syntax(sub)

            # Also check imported packages declared in this syntax tree
            if formals is None:
                scope = ctx.scope()
                while scope is not None and formals is None:
                    for pkg_name, imported_name in scope.imports:
                        if imported_name is not None and imported_name != callee_name:
                            continue
                        root = invocation
                        while getattr(root, "parent", None) is not None:
                            root = root.parent
                        for m in getattr(root, "members", ()):
                            if getattr(m, "kind", None) == sl.SyntaxKind.PackageDeclaration:
                                p_name = identifier_name(getattr(m.header, "name", None)) or str(m.header.name).strip()
                                if p_name == pkg_name:
                                    sub = _find_subroutine_in_container_syntax(m, callee_name)
                                    if sub is not None:
                                        formals = extract_formals_from_subroutine_syntax(sub)
                                        break
                        if formals is not None:
                            break
                    scope = scope.parent

    if not formals:
        return None

    # Match argument position or name to formal direction
    if type(arg_node).__name__ == "OrderedArgumentSyntax":
        ordered_args = [a for a in getattr(arg_list, "parameters", ()) if type(a).__name__ == "OrderedArgumentSyntax"]
        if arg_node in ordered_args:
            idx = ordered_args.index(arg_node)
            if idx < len(formals):
                return formals[idx][1]
    elif type(arg_node).__name__ == "NamedArgumentSyntax":
        arg_name = str(getattr(getattr(arg_node, "name", None), "value", "") or getattr(arg_node, "name", "")).strip()
        for f_name, f_dir in formals:
            if f_name == arg_name:
                return f_dir

    return None
