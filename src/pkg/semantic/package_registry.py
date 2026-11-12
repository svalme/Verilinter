"""The corpus-wide record of package declarations, and the stand-in package scopes seeded from it.

A file's own walk resolves `import pkg::*;` and `pkg::name` against packages declared in other files, so
the packages are recorded in a first pass (`record_packages_from_symbol_table`), fingerprinted for the
analysis-store cache key, and seeded into each file's symbol table before its walk.
"""
from __future__ import annotations

import json
from typing import Any

from .scope import Scope
from .scope_kinds import SUBROUTINE_SCOPE_KINDS, ScopeKind
from .symbol import Symbol
from .symbol_kind import SymbolKind
from .symbol_table import SymbolTable


def record_packages_from_symbol_table(
    file_path: str,
    symbol_table: SymbolTable,
    registry: dict[str, list[dict[str, Any]]],
) -> None:
    for name, scopes in symbol_table.packages.items():
        for scope in scopes:
            symbols = [
                {
                    "name": symbol.name,
                    "kind": symbol.kind,
                    "value": symbol.value,
                    "bit_width": symbol.bit_width,
                    "is_signed": symbol.is_signed,
                    "declarations": [dict(d) for d in symbol.declarations],
                }
                for symbol in scope.symbols.values()
                if symbol.is_declared
            ]
            subroutines = [
                {
                    "name": child.name,
                    "kind": child.kind,
                    "formals": [
                        {
                            "name": s.name,
                            "direction": s.port_direction,
                            "declarations": [dict(d) for d in s.declarations],
                        }
                        for s in child.symbols.values()
                        if s.is_port and not s.is_function_return and s.name != child.name
                    ],
                }
                for child in scope.children
                if child.kind in SUBROUTINE_SCOPE_KINDS
            ]
            registry.setdefault(name, []).append(
                {"file": file_path, "symbols": symbols, "subroutines": subroutines}
            )


def fingerprint_package_registry(registry: dict[str, list[dict[str, Any]]]) -> str | None:
    """Stable fingerprint of `_scan_packages`' output for the analysis-store cache
    key: a cached per-file result was resolved against a specific corpus-wide set
    of package declarations, and any of those changing (even in a different file)
    can change what a package-qualified/wildcard-imported name resolves to for
    the cached file -- see `seed_cross_file_packages`."""
    if not registry:
        return None
    payload = {
        name: sorted(
            (
                entry["file"],
                tuple(
                    sorted(
                        (s["name"], s["kind"], s.get("value"), s.get("bit_width"), s.get("is_signed"))
                        for s in entry["symbols"]
                    )
                ),
                tuple(
                    sorted(
                        (
                            sub["name"],
                            sub["kind"],
                            tuple(sorted((f["name"], f.get("direction")) for f in sub.get("formals", []))),
                        )
                        for sub in entry.get("subroutines", [])
                    )
                ),
            )
            for entry in entries
        )
        for name, entries in registry.items()
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def seed_cross_file_packages(
    symbol_table: SymbolTable,
    package_registry: dict[str, list[dict[str, Any]]] | None,
    current_file: str,
) -> None:
    """Seed `symbol_table.packages` with packages declared in OTHER input files
    (from `_scan_packages`), so this file's own single-file walk can resolve
    `import pkg::*;`/`pkg::name` against a package it doesn't declare itself.

    Skips any entry declared in `current_file`: that package is about to be
    (re)built with full fidelity by this file's own real walk, which must win
    over the leaner prepass-only stand-in. These stand-in scopes are
    deliberately never added to `symbol_table.scopes`, so they stay invisible
    to rules that iterate every scope actually declared in this file
    (NO_IMPLICIT_NET, NO_UNUSED_PARAMETER, ...).
    """
    if not package_registry:
        return
    for name, entries in package_registry.items():
        for entry in entries:
            if entry["file"] == current_file:
                continue
            scope = Scope(kind=ScopeKind.PACKAGE, name=name)
            scope.file = entry["file"]
            scope.packages = symbol_table.packages
            for symbol_data in entry["symbols"]:
                symbol = Symbol(name=str(symbol_data["name"]), kind=str(symbol_data.get("kind", "variable")))
                if symbol_data.get("value") is not None:
                    try:
                        symbol.value = int(symbol_data["value"])
                    except (ValueError, TypeError):
                        pass
                if symbol_data.get("bit_width") is not None:
                    try:
                        symbol.bit_width = int(symbol_data["bit_width"])
                    except (ValueError, TypeError):
                        pass
                if symbol_data.get("is_signed") is not None:
                    symbol.is_signed = bool(symbol_data["is_signed"])
                decls = symbol_data.get("declarations")
                if decls:
                    for d in decls:
                        symbol.add_declaration(dict(d))
                else:
                    symbol.add_declaration({"file": entry["file"]})
                scope.define(symbol)
            for sub_data in entry.get("subroutines", []):
                sub_scope = Scope(kind=str(sub_data.get("kind", "task")), name=str(sub_data.get("name", "")))
                sub_scope.file = entry["file"]
                for f in sub_data.get("formals", []):
                    formal_sym = Symbol(name=str(f["name"]), kind=SymbolKind.VARIABLE)
                    formal_sym.is_port = True
                    formal_sym.port_direction = f.get("direction")
                    decls = f.get("declarations")
                    if decls:
                        for d in decls:
                            formal_sym.add_declaration(dict(d))
                    else:
                        formal_sym.add_declaration({"file": entry["file"]})
                    sub_scope.define(formal_sym)
                sub_scope.set_parent(scope)
            symbol_table.packages.setdefault(name, []).append(scope)
