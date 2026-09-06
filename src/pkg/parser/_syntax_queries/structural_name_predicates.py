from ..syntax_kinds import (
    BIND_DIRECTIVE_KIND,
    COVER_CROSS_KIND,
    DEFPARAM_ASSIGNMENT_KIND,
    DISABLE_STATEMENT_KIND,
    EXTENDS_CLAUSE_KIND,
    FUNCTION_PROTOTYPE_KIND,
    INVOCATION_EXPRESSION_KIND,
    NAMED_TYPE_KIND,
    SCOPED_NAME_KIND,
)


def is_bind_directive_target(raw: object) -> bool:
    """True if `raw` is the target-module-name identifier of a `bind` directive.

    That identifier names a module/scope, not a variable, so it must not be treated
    as an ordinary identifier read (which would otherwise register it as an implicit net).
    """
    parent = getattr(raw, "parent", None)
    if getattr(parent, "kind", None) != BIND_DIRECTIVE_KIND:
        return False
    return getattr(parent, "target", None) is raw


def is_subroutine_prototype_name(raw: object) -> bool:
    """True if `raw` is the declared name of a task/function prototype
    (`FunctionPrototypeSyntax.name`, shared by both `TaskDeclarationSyntax` and
    `FunctionDeclarationSyntax` -- pyslang uses one prototype node for both).

    That identifier declares the subroutine's name, not a variable read, so it must
    not be treated as an ordinary identifier reference (which would otherwise
    register it as an implicit net).
    """
    parent = getattr(raw, "parent", None)
    if getattr(parent, "kind", None) != FUNCTION_PROTOTYPE_KIND:
        return False
    return getattr(parent, "name", None) is raw


def _is_scoped_name_target(raw: object, owner_kind: object, field: str = "name") -> bool:
    """Walk up through any chain of `ScopedNameSyntax` segments (`a.b.c`) from `raw`
    and return True if the outermost segment is the `field` field of a node whose
    kind is `owner_kind`. Shared by defparam-target and similar hierarchical-path
    checks below. `field` defaults to `"name"`, the common case; pass e.g.
    `field="left"` for owners (like `InvocationExpressionSyntax`) that use a
    different field name for the name/path in this position."""
    node = getattr(raw, "parent", None)
    while node is not None and getattr(node, "kind", None) == SCOPED_NAME_KIND:
        parent = getattr(node, "parent", None)
        if getattr(parent, "kind", None) == owner_kind and getattr(parent, field, None) is node:
            return True
        node = parent
    return getattr(node, "kind", None) == owner_kind and getattr(node, field, None) is raw


def is_defparam_target(raw: object) -> bool:
    """True if `raw` is (or is a `ScopedNameSyntax` segment of) the hierarchical
    target of a `defparam` assignment (`defparam a.b.c = ...;`).

    That identifier chain names a hierarchical parameter-override path, not a
    variable read, so it must not be treated as an ordinary identifier reference
    (which would otherwise register the trailing segment as an implicit net).
    """
    return _is_scoped_name_target(raw, DEFPARAM_ASSIGNMENT_KIND)


def is_disable_statement_target(raw: object) -> bool:
    """True if `raw` is (or is a `ScopedNameSyntax` segment of) the block/task
    label named by a `disable` statement (`disable blk;` / `disable pkg::blk;`).

    That identifier names a structural label, not a variable read, so it must not
    be treated as an ordinary identifier reference.
    """
    return _is_scoped_name_target(raw, DISABLE_STATEMENT_KIND)


def is_named_type_reference(raw: object) -> bool:
    """True if `raw` is (or is a `ScopedNameSyntax` segment of) the type name in a
    `NamedTypeSyntax` (a plain typedef'd type `my_t v;`, or a package-scoped type
    `pkg::my_t v;`).

    That identifier names a type, not a variable, so it must not be treated as an
    ordinary identifier reference -- unlike the other structural-name cases here,
    this one is not gated behind any already-banned construct, so it can misfire
    on completely ordinary, rule-compliant RTL using a typedef.
    """
    return _is_scoped_name_target(raw, NAMED_TYPE_KIND)


def is_invocation_callee(raw: object) -> bool:
    """True if `raw` is (or is a `ScopedNameSyntax` segment of) the callee name of
    a function/task/`let` call (`InvocationExpressionSyntax.left`, e.g. `f(1, 2)`
    or `pkg::f(1, 2)`).

    That identifier names the thing being called, not a variable being read, so it
    must not be treated as an ordinary identifier reference. Companion to
    `is_subroutine_prototype_name`, which only covers the *declaration* name --
    without this, calling any subroutine (including a DPI import, which has no
    banning rule at all) produces a false implicit net at the call site.
    """
    return _is_scoped_name_target(raw, INVOCATION_EXPRESSION_KIND, field="left")


def is_cover_cross_item(raw: object) -> bool:
    """True if `raw` is one of the coverpoint-label arguments of a `cross`
    statement (`CoverCrossSyntax.items`, e.g. `cpx`/`cpy` in `crs: cross cpx, cpy;`).

    Those identifiers name previously-declared coverpoint labels, not variables.
    """
    return getattr(getattr(raw, "parent", None), "kind", None) == COVER_CROSS_KIND


def is_extends_clause_base_name(raw: object) -> bool:
    """True if `raw` is (or is a `ScopedNameSyntax` segment of) the base-class name
    in a class `extends` clause (`class C extends Base;` / `class C extends pkg::Base;`).

    That identifier names a class, not a variable.
    """
    return _is_scoped_name_target(raw, EXTENDS_CLAUSE_KIND, field="baseName")
