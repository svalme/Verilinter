"""Symbol kinds are an enum, and what a kind implies lives on the enum and on `Symbol`, not in each rule."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_kind import SymbolKind

SRC_DIR = Path(__file__).resolve().parent.parents[2] / "src" / "pkg"
KIND_VALUES = {kind.value for kind in SymbolKind}


def test_symbol_coerces_a_kind_string_to_the_enum() -> None:
    symbol = Symbol(name="x", kind="parameter")

    assert symbol.kind is SymbolKind.PARAMETER


def test_symbol_rejects_a_kind_that_is_not_in_the_enum() -> None:
    with pytest.raises(ValueError):
        Symbol(name="x", kind="wire")


@pytest.mark.parametrize(
    ("kind", "is_constant"),
    [
        (SymbolKind.PARAMETER, True),
        (SymbolKind.ENUM_MEMBER, True),
        (SymbolKind.VARIABLE, False),
        (SymbolKind.FIELD, False),
        (SymbolKind.TYPEDEF, False),
        (SymbolKind.GENVAR, False),
        (SymbolKind.INSTANCE, False),
        (SymbolKind.IMPLICIT_NET, False),
    ],
)
def test_kind_says_whether_it_is_a_compile_time_constant(kind: SymbolKind, is_constant: bool) -> None:
    assert kind.is_compile_time_constant is is_constant


def test_only_a_typedef_is_a_type_name() -> None:
    assert [kind for kind in SymbolKind if kind.is_type_name] == [SymbolKind.TYPEDEF]


def test_symbol_is_a_compile_time_constant_by_kind_or_flag() -> None:
    assert Symbol("p", SymbolKind.PARAMETER).is_compile_time_constant
    assert Symbol("e", SymbolKind.ENUM_MEMBER).is_compile_time_constant
    assert not Symbol("v", SymbolKind.VARIABLE).is_compile_time_constant

    flagged = Symbol("v", SymbolKind.VARIABLE)
    flagged.is_constant = True
    assert flagged.is_compile_time_constant

    local = Symbol("l", SymbolKind.VARIABLE)
    local.is_localparam = True
    assert local.is_compile_time_constant


def _string_values(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [value for element in node.elts for value in _string_values(element)]
    return []


def test_symbol_kinds_are_not_written_as_string_literals_in_source() -> None:
    """A rule that asks about a kind uses `SymbolKind` or a property such as `is_compile_time_constant`,
    so a new guard cannot disagree with an existing one about which kinds count."""
    offenders: list[str] = []
    for path in sorted(SRC_DIR.rglob("*.py")):
        relative = path.relative_to(SRC_DIR).as_posix()
        if relative == "semantic/symbol_kind.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                touches_kind = any(isinstance(side, ast.Attribute) and side.attr == "kind" for side in [node.left, *node.comparators])
                literals = [value for side in [node.left, *node.comparators] for value in _string_values(side)]
                if touches_kind and KIND_VALUES.intersection(literals):
                    offenders.append(f"{relative}:{node.lineno} compares .kind with a symbol-kind string")
            elif isinstance(node, ast.Call):
                callee = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                if callee == "is_explicit_kind" and any(KIND_VALUES.intersection(_string_values(arg)) for arg in node.args):
                    offenders.append(f"{relative}:{node.lineno} is_explicit_kind with a string")
                if callee == "Symbol":
                    for keyword in node.keywords:
                        if keyword.arg == "kind" and KIND_VALUES.intersection(_string_values(keyword.value)):
                            offenders.append(f"{relative}:{node.lineno} Symbol(kind=<string>)")
    assert offenders == [], offenders
