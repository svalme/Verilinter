from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...vnodes.base_vnode import Location
    from .assignment_target import AssignmentTarget


class AssignmentKind(StrEnum):
    BLOCKING = "blocking"
    NONBLOCKING = "nonblocking"
    CONTINUOUS = "continuous"
    INITIALIZER = "initializer"
    COMPOUND = "compound"  # `x += y`: reads and writes its target


@dataclass(frozen=True)
class AssignmentRecord:
    """One assignment-like construct, taken apart once.

    `targets` has one entry per written reference: a concatenated left-hand side gives several, in
    source order. A name with no declaration refers to the placeholder symbol the resolver records (`is_declared` False). `rhs` is the right-hand
    side node. `driver_id` and `driver_location` name the enclosing procedural block or continuous
    assign, in the form the use events record them.
    """

    node: object
    kind: AssignmentKind
    targets: tuple[AssignmentTarget, ...]
    rhs: object | None
    driver_id: str | None
    driver_location: Location | None
    statement_id: str
    location: Location | None

    def combined_target(self) -> AssignmentTarget | None:
        """The written value as one target for width and signedness checks, or None when it cannot be
        sized: no target, a name with no symbol, or (for a concatenation) a member whose width is unknown.
        A single reference is returned as it is; several are joined, widths added."""
        from .assignment_target import AssignmentTarget

        if not self.targets or any(target.base_symbol is None for target in self.targets):
            return None
        if len(self.targets) == 1:
            return self.targets[0]
        widths = [target.bit_width for target in self.targets]
        if not all(isinstance(width, int) for width in widths):
            return None
        return AssignmentTarget(is_concatenated=True, elements=list(self.targets), total_width=sum(widths))
