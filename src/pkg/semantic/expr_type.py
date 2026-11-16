"""The width and signedness of an expression, with how its width is decided.

A rule asks the `ExprType` a question (`differs_from`) and does not combine a width with separate flags
itself, so a new way of deciding a width changes one method.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WidthDetermination(StrEnum):
    SELF = "self"  # the width is the expression's own: a name, a select, a concatenation, a literal
    CONTEXT = "context"  # a result that can outgrow its operands (`+`, `*`, `<<`): the target's width decides
    ADAPTS = "adapts"  # a literal with no width of its own (`'0`, `0`): it fills the target, so there is nothing to size

    @classmethod
    def of(cls, grows_with_context: bool) -> WidthDetermination:
        return cls.CONTEXT if grows_with_context else cls.SELF


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

        A result that can outgrow its operands is computed at the target's width when that is wider, so
        only a wider one differs."""
        if not isinstance(self.width, int) or not isinstance(target_width, int):
            return False
        if self.width == target_width:
            return False
        if self.determination is WidthDetermination.CONTEXT and self.width < target_width:
            return False
        return True
