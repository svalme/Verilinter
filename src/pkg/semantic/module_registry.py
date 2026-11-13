"""The corpus-wide record of each module's ports, seeded into every file's symbol table.

An instance in one file connects to a module declared in another, and the file's own walk needs the
module's port directions to tell a driven signal from a read one. The ports are recorded in a first pass
(`record_module_ports`), fingerprinted for the analysis-store cache key, and attached to
each file's symbol table before its walk (`seed_cross_file_module_ports`).
"""
from __future__ import annotations

import json
from typing import Any

from .symbol_table import SymbolTable


def record_module_ports(
    file_path: str,
    ports_by_module: dict[str, list[tuple[str, str | None]]],
    registry: dict[str, list[dict[str, Any]]],
) -> None:
    for name, ports in ports_by_module.items():
        registry.setdefault(name, []).append(
            {"file": file_path, "ports": [{"name": port, "direction": direction} for port, direction in ports]}
        )


def fingerprint_module_ports(registry: dict[str, list[dict[str, Any]]] | None) -> str | None:
    """Stable fingerprint of the registry for the analysis-store cache key: a cached per-file result was
    classified against specific port directions, and a change in any file can change it."""
    if not registry:
        return None
    payload = {
        name: sorted(
            (entry["file"], [(port["name"], port.get("direction")) for port in entry["ports"]])
            for entry in entries
        )
        for name, entries in registry.items()
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def seed_cross_file_module_ports(
    symbol_table: SymbolTable,
    module_ports: dict[str, list[dict[str, Any]]] | None,
    current_file: str,
) -> None:
    """Attach the ports of modules declared in OTHER files to `symbol_table.module_ports`. A module
    declared in `current_file` is found through `symbol_table.modules` with full fidelity, so it is left out."""
    if not module_ports:
        return
    for name, entries in module_ports.items():
        others = [entry for entry in entries if entry["file"] != current_file]
        if others:
            symbol_table.module_ports[name] = others
