"""Answers what the symbol table knows about a package: its scopes, a member name and a subroutine."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .scope_kinds import SUBROUTINE_SCOPE_KINDS
from .symbol import Symbol

if TYPE_CHECKING:
    from .scope import Scope


class PackageResolver:
    """Looks a package up by name in the table's package registry, which holds every scope that declares it:
    the scope walked in this file and a stand-in scope for each package declared in another input file
    (`Scope.is_stand_in`).

    A member or a subroutine is looked up in the declaring scopes only, in registration order, so an outer
    name of the same spelling is never found. A package no analysed file declares has no scope: `scope`
    and `member` give None and `is_declared` is False, which the caller treats as "may come from an
    unseen package", not as "the name does not exist". It reads the registry and never changes it.
    """

    __slots__ = ("_packages",)

    def __init__(self, packages: dict[str, list[Scope]] | None) -> None:
        self._packages = packages or {}

    def scopes(self, name: str) -> list[Scope]:
        """Every scope that declares the package, or an empty list."""
        return self._packages.get(name, [])

    def scope(self, name: str) -> Scope | None:
        """The first scope that declares the package, for a caller that needs the package itself."""
        scopes = self.scopes(name)
        return scopes[0] if scopes else None

    def is_declared(self, name: str) -> bool:
        return name in self._packages

    def member(self, package: str, name: str) -> Symbol | None:
        """`package::name`: the symbol the package declares, or None when the package or the name is not known."""
        for package_scope in self.scopes(package):
            found = package_scope.lookup(name)
            if found is not None:
                return found
        return None

    def subroutine(self, package: str, name: str) -> Scope | None:
        """The scope of the task or function `package::name`, or None."""
        for package_scope in self.scopes(package):
            for child in package_scope.children:
                if child.kind in SUBROUTINE_SCOPE_KINDS and child.name == name:
                    return child
        return None
