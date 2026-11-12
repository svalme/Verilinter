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
