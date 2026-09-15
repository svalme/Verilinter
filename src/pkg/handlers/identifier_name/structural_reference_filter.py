from __future__ import annotations

from collections.abc import Callable, Sequence

from ...parser.syntax import (
    is_bind_directive_target,
    is_cover_cross_item,
    is_defparam_target,
    is_disable_statement_target,
    is_extends_clause_base_name,
    is_invocation_callee,
    is_member_selector,
    is_named_type_reference,
    is_scoped_name_qualifier,
    is_subroutine_prototype_name,
)

# Every check here recognizes an IdentifierNameSyntax-shaped node that names a
# module/scope/type/label/callee/parameter-path rather than a variable being read
# or written. Each was found the same way: some rule/audit exercised a construct
# IdentifierNameHandler had never been taught about, and the identifier fell
# through to implicit-net creation. Add to this list rather than inlining another
# `or` clause -- it is expected to keep growing.
DEFAULT_STRUCTURAL_NAME_PREDICATES: tuple[Callable[[object], bool], ...] = (
    is_bind_directive_target,
    is_subroutine_prototype_name,
    is_defparam_target,
    is_disable_statement_target,
    is_named_type_reference,
    is_invocation_callee,
    is_cover_cross_item,
    is_extends_clause_base_name,
    is_scoped_name_qualifier,
    is_member_selector,
)


class StructuralReferenceFilter:
    """Filters AST identifier nodes representing structural syntax references

    (such as type names, subroutine callee names, labels, member selectors)
    rather than signals, variables, or nets being read or written.
    """

    def __init__(
        self,
        predicates: Sequence[Callable[[object], bool]] | None = None,
    ) -> None:
        self._predicates = (
            tuple(predicates)
            if predicates is not None
            else DEFAULT_STRUCTURAL_NAME_PREDICATES
        )

    @property
    def predicates(self) -> tuple[Callable[[object], bool], ...]:
        return self._predicates

    def is_structural_reference(self, raw: object) -> bool:
        return any(predicate(raw) for predicate in self._predicates)
