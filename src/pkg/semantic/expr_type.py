"""The width and signedness of an expression, with how its width is decided.

A rule asks the `ExprType` a question (`differs_from`) and does not combine a width with separate flags
itself, so a new way of deciding a width changes one method.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WidthDetermination(StrEnum):
    SELF = "self"  # the width is the expression's own: a name, a select, a concatenation, a literal
    CONTEXT = "context"  # an operator whose operands are widened to the width of the target (IEEE 1800 11.6)


@dataclass(frozen=True)
class ExprType:
    width: int | None = None
    signed: bool | None = None
    determination: WidthDetermination = WidthDetermination.SELF

    @property
    def is_width_known(self) -> bool:
        return isinstance(self.width, int)

    def differs_from(self, target_width: int | None) -> bool:
        """True when both widths are known and the value would not simply fit the target.

        An expression whose operands take the target's width is extended when it is narrower, so only a
        wider one differs."""
        if not isinstance(self.width, int) or not isinstance(target_width, int):
            return False
        if self.width == target_width:
            return False
        if self.determination is WidthDetermination.CONTEXT and self.width < target_width:
            return False
        return True
