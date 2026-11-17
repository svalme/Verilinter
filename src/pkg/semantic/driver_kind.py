"""What owns the writes of a driver: a continuous assign, a kind of procedural block, or something else."""
from __future__ import annotations

from enum import StrEnum


class DriverKind(StrEnum):
    """Values equal the categories the parser reports for a driver block (`driver_block_category`)."""

    CONTINUOUS = "continuous"  # a continuous assign, including a tri-state one
    INITIAL = "initial"  # an initial block: its writes happen at time 0
    SEQUENTIAL = "sequential"  # a clocked procedural block
    COMBINATIONAL = "combinational"  # always_comb, or an always block sensitive to levels
    ALWAYS = "always"  # any other always block, such as always_latch
    OTHER = "other"  # a block that is none of these, such as a final block

    @property
    def is_procedural_always(self) -> bool:
        """The writes are made by a synthesizable always block."""
        return self in (DriverKind.SEQUENTIAL, DriverKind.COMBINATIONAL, DriverKind.ALWAYS)
