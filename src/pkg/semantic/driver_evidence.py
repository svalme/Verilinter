# src/pkg/semantic/driver_evidence.py
from __future__ import annotations

from enum import Enum


class DriverEvidence(Enum):
    """What this file shows about who drives a symbol. The members are ordered by precedence: a symbol
    with several kinds of evidence has the first that applies."""

    UNSEEN = "unseen"  # something this file cannot see may drive it, so a missing driver is not established
    INSTANCE = "instance"  # an output or inout port of an instance drives it
    WRITTEN = "written"  # a write in this file drives it
    NONE = "none"  # no driver is visible and none is possible outside this file

    @property
    def is_driver_established(self) -> bool:
        """A driver is known to exist, in this file or through an instance."""
        return self in (DriverEvidence.INSTANCE, DriverEvidence.WRITTEN)
