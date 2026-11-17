"""Bit widths slang computes for every expression of an elaborated file set.

The record is read-only data keyed by the source span of an expression. A span visited under several
instances of one module (parameter overrides differ) keeps every width it had, so a reader can tell a
single answer from a disagreement. Implicit conversions are skipped: they carry the width the context
forced, while the operand under them keeps its own."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import os
from pathlib import Path

import pyslang as sl

SpanKey = tuple[str, int, int]

_EXPLICIT_CONVERSION = sl.ConversionKind.Explicit


def _normal_path(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


@dataclass(frozen=True)
class ElaboratedWidth:
    """Every width and signedness one source span had across the elaborated instances."""

    widths: frozenset[int]
    signed: frozenset[bool]

    @property
    def width(self) -> int | None:
        """The width when every instance agrees, else None."""
        return next(iter(self.widths)) if len(self.widths) == 1 else None

    @property
    def is_signed(self) -> bool | None:
        return next(iter(self.signed)) if len(self.signed) == 1 else None


class ElaboratedWidths:
    def __init__(self) -> None:
        self._widths: dict[tuple[SpanKey, bool], set[int]] = {}
        self._signed: dict[tuple[SpanKey, bool], set[bool]] = {}
        self.file_count = 0
        self.error_count = 0

    @classmethod
    def build(
        cls,
        paths: Iterable[str | Path],
        include_dirs: list[str] | None = None,
        defines: list[str] | None = None,
    ) -> "ElaboratedWidths":
        """Parse `paths` under one source manager, elaborate them together and record every expression."""
        record = cls()
        source_manager = sl.SourceManager()
        for directory in include_dirs or []:
            source_manager.addUserDirectories(directory)
        bag = sl.Bag()
        if defines:
            preprocessor = sl.PreprocessorOptions()
            preprocessor.predefines = list(defines)
            bag.preprocessorOptions = preprocessor
        compilation = sl.Compilation(bag)
        for path in paths:
            compilation.addSyntaxTree(sl.SyntaxTree.fromFile(str(path), source_manager, options=bag))
            record.file_count += 1
        record.error_count = sum(1 for d in compilation.getAllDiagnostics() if d.isError())
        manager = compilation.sourceManager
        compilation.getRoot().visit(lambda node: record._add(node, manager))
        return record

    def _add(self, node: object, manager: sl.SourceManager) -> None:
        if not isinstance(node, sl.Expression):
            return
        if node.kind == sl.ExpressionKind.Conversion and node.conversionKind != _EXPLICIT_CONVERSION:
            return
        start = node.sourceRange.start
        end = node.sourceRange.end
        if start == sl.SourceLocation.NoLocation or manager.isMacroLoc(start) or manager.isMacroLoc(end):
            return
        node_type = node.type
        if node_type is None or not node_type.isIntegral:
            return
        span = (_normal_path(manager.getFileName(start)), start.offset, end.offset)
        key = (span, node.kind == sl.ExpressionKind.NamedValue)
        self._widths.setdefault(key, set()).add(node_type.bitWidth)
        self._signed.setdefault(key, set()).add(bool(node_type.isSigned))

    def widths_at(self, path: str | Path, start: int, end: int) -> ElaboratedWidth | None:
        span = (_normal_path(path), start, end)
        # A name inside a member access or select reports the range of the whole access, so a
        # non-name node on the same span is the expression itself and wins over the name.
        key = (span, False) if (span, False) in self._widths else (span, True)
        widths = self._widths.get(key)
        if widths is None:
            return None
        return ElaboratedWidth(frozenset(widths), frozenset(self._signed[key]))

    def __len__(self) -> int:
        return len({span for span, _is_name in self._widths})
