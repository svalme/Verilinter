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
_MAX_SCOPES_PER_TOP = 1_000_000  # bound on the instance and generate scopes walked under one top-level instance
_PAYLOAD_LAYOUT = 1  # the shape `to_payload` writes; `from_payload` refuses another


def _connected_width(expression: object) -> int | None:
    """The width of the expression a port connection names. Slang wraps an input's expression in an implicit
    conversion to the port type and an output's in an assignment; the width wanted is the written expression's."""
    node = expression
    if node is not None and node.kind == sl.ExpressionKind.Assignment:
        node = node.left
    steps = 0
    while node is not None and node.kind == sl.ExpressionKind.Conversion and node.conversionKind != _EXPLICIT_CONVERSION and steps < 64:
        node = node.operand
        steps += 1
    if node is None or not node.type.isIntegral:
        return None
    return node.type.bitWidth


def _pair_order(pair: list[int | None]) -> tuple[int, int]:
    return (pair[0] or 0, -1 if pair[1] is None else pair[1])


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
        # (parent module, instance name, port name) -> (port width, connected expression width) of each elaborated instance
        self._connections: dict[tuple[str, str, str], set[tuple[int, int | None]]] = {}
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
        for top in compilation.getRoot().topInstances:
            record._add_connections(top)
        return record

    def _add_connections(self, top: object) -> None:
        """Record every port connection of the instances under `top`, keyed by the module that instantiates
        them, so a connection is found without a source position."""
        pending = [(top.body, top.definition.name)]
        scopes_visited = 0
        while pending and scopes_visited < _MAX_SCOPES_PER_TOP:
            scopes_visited += 1
            scope, parent_module = pending.pop()
            for member in scope:
                kind = member.kind
                if kind == sl.SymbolKind.Instance:
                    self._add_instance(member, parent_module, member.name)
                    pending.append((member.body, member.definition.name))
                elif kind == sl.SymbolKind.InstanceArray:
                    for element in member:
                        self._add_instance(element, parent_module, member.name)
                        pending.append((element.body, element.definition.name))
                elif kind in (sl.SymbolKind.GenerateBlock, sl.SymbolKind.GenerateBlockArray):
                    pending.append((member, parent_module))

    def _add_instance(self, instance: object, parent_module: str, name: str) -> None:
        for connection in instance.portConnections:
            port_type = connection.port.type
            if not port_type.isIntegral:
                continue
            expression_width = _connected_width(connection.expression)
            key = (parent_module, name, connection.port.name)
            self._connections.setdefault(key, set()).add((port_type.bitWidth, expression_width))

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

    def connection_widths(self, parent_module: str | None, instance: str | None, port: str | None) -> frozenset[tuple[int, int | None]]:
        """`(port width, connected expression width)` of the connection in each elaborated instance, or an
        empty set when slang elaborated no instance of that name in that module."""
        if not (parent_module and instance and port):
            return frozenset()
        return frozenset(self._connections.get((parent_module, instance, port), ()))

    def widths_for(self, node: object, tree: object) -> ElaboratedWidth | None:
        """The widths of a syntax node of `tree`, read from the span of the node, or None when slang has no entry."""
        span = getattr(node, "sourceRange", None)
        manager = getattr(tree, "sourceManager", None)
        if span is None or manager is None or span.start == sl.SourceLocation.NoLocation:
            return None
        return self.widths_at(manager.getFileName(span.start), span.start.offset, span.end.offset)

    def is_macro_expansion(self, node: object, tree: object) -> bool:
        """The node was produced by a macro expansion, so its span names no text of its own file."""
        span = getattr(node, "sourceRange", None)
        manager = getattr(tree, "sourceManager", None)
        if span is None or manager is None:
            return False
        return bool(manager.isMacroLoc(span.start) or manager.isMacroLoc(span.end))

    def __len__(self) -> int:
        return len({span for span, _is_name in self._widths})

    def to_payload(self) -> dict:
        """The record as plain data, for the elaboration cache. Paths are listed once and spans refer to them."""
        files: dict[str, int] = {}
        spans = []
        for (span, is_name), widths in self._widths.items():
            path, start, end = span
            index = files.setdefault(path, len(files))
            signed = sorted(int(flag) for flag in self._signed[(span, is_name)])
            spans.append([index, start, end, int(is_name), sorted(widths), signed])
        connections = [
            [parent, instance, port, sorted(([port_width, expr_width] for port_width, expr_width in pairs), key=_pair_order)]
            for (parent, instance, port), pairs in self._connections.items()
        ]
        return {
            "layout": _PAYLOAD_LAYOUT,
            "files": list(files),
            "spans": spans,
            "port_width_pairs": connections,
            "file_count": self.file_count,
            "error_count": self.error_count,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "ElaboratedWidths":
        """Rebuild a record from `to_payload` data. Raises ValueError for data of another layout or shape."""
        if payload.get("layout") != _PAYLOAD_LAYOUT:
            raise ValueError("elaboration cache payload has another layout")
        record = cls()
        try:
            files = [str(path) for path in payload["files"]]
            for index, start, end, is_name, widths, signed in payload["spans"]:
                key = ((files[index], int(start), int(end)), bool(is_name))
                record._widths[key] = {int(width) for width in widths}
                record._signed[key] = {bool(flag) for flag in signed}
            for parent, instance, port, pairs in payload["port_width_pairs"]:
                record._connections[(str(parent), str(instance), str(port))] = {
                    (int(port_width), None if expr_width is None else int(expr_width)) for port_width, expr_width in pairs
                }
            record.file_count = int(payload["file_count"])
            record.error_count = int(payload["error_count"])
        except (KeyError, IndexError, TypeError, ValueError) as error:
            raise ValueError(f"elaboration cache payload is malformed: {error}") from error
        return record
