from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..symbol import Symbol


class AssignmentTarget:
    """Represents a resolved target of an assignment construct.

    Unifies whole-symbol targets (`assign a = ...;`) with indexed, sliced, or
    part-selected targets (`assign a[i] = ...;`, `assign a[7:0] = ...;`).

    Delegates all other symbol attributes (declarations, uses, scope, etc.)
    transparently to `base_symbol`.
    """

    def __init__(
        self,
        base_symbol: Symbol,
        slice_width: int | None = None,
        is_sliced: bool = False,
        selectors: list[object] | None = None,
    ) -> None:
        self.base_symbol = base_symbol
        self.slice_width = slice_width
        self.is_sliced = is_sliced
        self.selectors = list(selectors or [])

    @property
    def bit_width(self) -> int | None:
        if self.is_sliced:
            return self.slice_width
        return getattr(self.base_symbol, "bit_width", None)

    @property
    def is_signed(self) -> bool | None:
        if self.is_sliced:
            return None
        return getattr(self.base_symbol, "is_signed", None)

    def __getattr__(self, name: str) -> object:
        return getattr(self.base_symbol, name)

    def __repr__(self) -> str:
        name = getattr(self.base_symbol, "name", "<unnamed>")
        if self.is_sliced:
            return f"AssignmentTarget({name}[...], width={self.bit_width})"
        return f"AssignmentTarget({name}, width={self.bit_width})"
