"""The outcome of looking up an identifier, and the record kept for a name that has no declaration."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from ..vnodes.base_vnode import Location

if TYPE_CHECKING:
    from .symbol import Symbol


class ResolutionStatus(StrEnum):
    RESOLVED = "resolved"  # a declaration was found
    UNRESOLVED_IMPLICIT_NET = "unresolved_implicit_net"  # no declaration; `default_nettype wire` makes it an implicit net
    UNRESOLVED_UNDECLARED = "unresolved_undeclared"  # no declaration; `default_nettype none` makes it an error
    UNRESOLVABLE_HERE = "unresolvable_here"  # package-qualified name this file cannot see into


@dataclass(frozen=True)
class Resolution:
    status: ResolutionStatus
    symbol: Symbol | None = None  # set when status is RESOLVED


@dataclass
class UnresolvedReference:
    """A name used without a declaration, recorded once at its first use.

    `symbol` is the placeholder that collects the name's uses. The reference counts as unresolved while the
    placeholder has no declaration, so a declaration that follows the first use (in the same scope) clears it.
    """

    name: str
    status: ResolutionStatus
    location: Location | None
    symbol: Symbol | None = None

    @property
    def is_unresolved(self) -> bool:
        if self.status is ResolutionStatus.UNRESOLVABLE_HERE or self.symbol is None:
            return False
        return not self.symbol.is_declared
