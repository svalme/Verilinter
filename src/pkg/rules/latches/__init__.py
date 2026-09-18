"""Latch-inference and always_latch usage rules."""

from .no_always_latch import NoAlwaysLatchRule
from .no_latch_in_always_latch import NoLatchInAlwaysLatchRule

__all__ = ["NoAlwaysLatchRule", "NoLatchInAlwaysLatchRule"]
