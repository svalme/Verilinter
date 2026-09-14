from ..syntax_kinds import DOUBLE_COLON_TOKEN_KIND, PACKAGE_IMPORT_DECLARATION_KIND, SCOPED_NAME_KIND, STAR_TOKEN_KIND
from .shapes import identifier_name


def _is_double_colon_scoped_name(node: object) -> bool:
    """True if `node` is a `ScopedNameSyntax` joined by `::`, not `.`.

    pyslang represents BOTH `pkg::name` package scope resolution AND
    `struct_var.field` member access with the same `ScopedNameSyntax` node --
    syntactically identical before elaboration can tell a namespace path from a
    struct/interface member path -- distinguished only by `.separator.kind`.
    Every predicate in this module must check this, or it will misfire on
    ordinary `var.field` member access (confirmed directly: `perms.U0` on a
    `perms_t` struct variable parses to a `ScopedNameSyntax` exactly like
    `pkg::name`, separator token `.` vs `::`).
    """
    if getattr(node, "kind", None) != SCOPED_NAME_KIND:
        return False
    separator = getattr(node, "separator", None)
    return getattr(separator, "kind", None) == DOUBLE_COLON_TOKEN_KIND


def is_scoped_name_qualifier(raw: object) -> bool:
    """True if `raw` is the left (namespace-qualifier) segment of a `pkg::name`
    scoped-name expression (`pkg::name`, `pkg::sub::name`, ...) -- never of the
    `.`-joined `var.field` member-access shape that shares the same node kind.

    The qualifier segment names a package/class scope, not a variable, so it must
    never be treated as an ordinary identifier reference (which would otherwise
    register it as an implicit net) -- unlike the other structural-name predicates
    in `structural_name_predicates.py`, this applies unconditionally to every
    `::`-joined scope-resolution qualifier, regardless of what the whole scoped
    name resolves to.
    """
    parent = getattr(raw, "parent", None)
    return _is_double_colon_scoped_name(parent) and getattr(parent, "left", None) is raw


def scoped_name_package_qualifier(raw: object) -> str | None:
    """If `raw` is the terminal (rightmost) identifier of a simple two-segment
    `pkg::name` scoped-name expression, return `"pkg"`; otherwise `None`.

    Deliberately narrow to the two-segment `::`-joined shape
    (`ScopedNameSyntax.left` a plain identifier, not itself a nested
    `ScopedNameSyntax`, and joined by `::` rather than `.` -- see
    `_is_double_colon_scoped_name`) -- this is the dominant shape
    for package-qualified references, and a deeper chain (`a::b::c`,
    e.g. nested class scope resolution) is deliberately left unresolved rather
    than guessed at.
    """
    parent = getattr(raw, "parent", None)
    if not _is_double_colon_scoped_name(parent) or getattr(parent, "right", None) is not raw:
        return None
    left = getattr(parent, "left", None)
    if getattr(left, "kind", None) == SCOPED_NAME_KIND:
        return None
    return identifier_name(left)


def package_import_items(raw: object) -> list[tuple[str, str | None]]:
    """Extract `(package_name, imported_name)` pairs from a
    `PackageImportDeclarationSyntax` (`import pkg::*;` / `import pkg::NAME;`).

    `imported_name` is `None` for the wildcard form. `.package`/`.item` are bare
    tokens, not `IdentifierNameSyntax` nodes, so `IdentifierNameHandler` never
    visits them -- this is the only place that reads them.
    """
    if getattr(raw, "kind", None) != PACKAGE_IMPORT_DECLARATION_KIND:
        return []
    items: list[tuple[str, str | None]] = []
    for item in getattr(raw, "items", None) or []:
        package_token = getattr(item, "package", None)
        package_name = getattr(package_token, "valueText", None)
        if not package_name:
            continue
        item_token = getattr(item, "item", None)
        if getattr(item_token, "kind", None) == STAR_TOKEN_KIND:
            items.append((package_name, None))
            continue
        item_name = getattr(item_token, "valueText", None)
        if item_name:
            items.append((package_name, item_name))
    return items
