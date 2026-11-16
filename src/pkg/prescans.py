"""The two sequential pre-scans that run before any per-file worker: the package registry and the module ports (`PIPELINE_REGISTER.md`)."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Sequence
from .analysis_store import file_sha256
from .parser.parse import extract_header_dependencies, extract_parse_diagnostics, file_uses_default_nettype_none, parse_file, tree_has_package_declaration
from .parser.syntax import instantiated_module_names, module_ports_in_file
from .rules.register_rules import *
from .store.keys import MODULE_PORT_SCAN_FINGERPRINT
from .semantic.module_registry import fingerprint_module_ports, record_module_ports
from .semantic.package_registry import fingerprint_package_registry, record_packages_from_symbol_table
from .semantic.symbol_table import SymbolTable
from .walk.context import Context
from .walk.dispatch import dispatch
from .walk.walker import Walker
from .handlers.register_handlers import *
from .vnodes.register_vnodes import *
from .workers import call_parse_file, get_override, warn_store_unavailable


def _file_may_declare_package(path: Path) -> bool:
    """Non-regex lexical prefilter so `scan_packages` avoids parsing files
    that contain no package keyword, preserving incremental cache hit assertions."""
    try:
        text = path.read_text(errors="ignore")
    except OSError:
        return False
    idx = 0
    kw = "package"
    kw_len = len(kw)
    while True:
        pos = text.find(kw, idx)
        if pos == -1:
            return False
        before_ok = (pos == 0) or not (text[pos - 1].isalnum() or text[pos - 1] in ("_", "$"))
        after_pos = pos + kw_len
        after_ok = (after_pos == len(text)) or not (text[after_pos].isalnum() or text[after_pos] in ("_", "$"))
        if before_ok and after_ok:
            return True
        idx = pos + kw_len


def scan_packages(
    paths: list[Path],
    include_dirs: list[str] | None = None,
    defines: Sequence[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """First pass over the corpus: find every `package ... endpackage`
    declaration and what it exports, before any per-file lint worker runs.

    NO_IMPLICIT_NET and friends resolve a package-qualified/wildcard-imported
    name during each file's OWN single-file walk (see identifier_name_handler.py),
    so package visibility has to be known before that walk starts -- unlike
    UNDEFINED_MODULE/DUPLICATE_MODULE, which reconcile module definitions
    across files only after every worker finishes (see
    `_build_cross_file_symbol_table`).
    """
    registry: dict[str, list[dict[str, Any]]] = {}
    for path in paths:
        if not _file_may_declare_package(path):
            continue
        _Walker = get_override("Walker", Walker)
        _parse_file = get_override("parse_file", parse_file)
        _file_uses_default_nettype_none = get_override("file_uses_default_nettype_none", file_uses_default_nettype_none)
        tree = call_parse_file(_parse_file, str(path), include_dirs=include_dirs, defines=defines)
        if extract_parse_diagnostics(tree, str(path)):
            continue
        if not tree_has_package_declaration(tree):
            continue
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = _Walker(dispatch)
        symbol_table.set_current_file(str(path))
        symbol_table.set_current_file_default_nettype_none(_file_uses_default_nettype_none(path))
        walker.walk(tree.root, tree, ctx, symbol_table)
        record_packages_from_symbol_table(str(path), symbol_table, registry)
    return registry


def scan_packages_from_trees(
    file_inputs: Sequence[tuple[str, Any]],
    default_nettype_none_by_file: dict[str, bool] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    registry: dict[str, list[dict[str, Any]]] = {}
    _Walker = get_override("Walker", Walker)
    for file_name, tree in file_inputs:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = _Walker(dispatch)
        symbol_table.set_current_file(file_name)
        symbol_table.set_current_file_default_nettype_none(
            (default_nettype_none_by_file or {}).get(file_name, False)
        )
        walker.walk(tree.root, tree, ctx, symbol_table)
        record_packages_from_symbol_table(file_name, symbol_table, registry)
    return registry


def scan_module_ports(
    paths: list[Path],
    include_dirs: list[str] | None = None,
    defines: Sequence[str] | None = None,
    store: Any = None,
    use_cache: bool = True,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[str]]]:
    """First pass over the corpus: record the ports of every module and the modules each file instantiates,
    from the syntax alone, so a file's own walk knows the port directions of the modules it instantiates
    (see `apply_instance_port_effects`). A file's result is kept in the analysis store under its hash, so an
    unchanged file is not parsed again. Returns the port registry and the instantiated modules per file."""
    registry: dict[str, list[dict[str, Any]]] = {}
    children_by_path: dict[str, list[str]] = {}
    _parse_file = get_override("parse_file", parse_file)
    for path in paths:
        key = {
            "file_path": str(path),
            "file_hash": file_sha256(path) if store is not None else "",
            "rule_selection": None,
            "include_dirs": include_dirs,
            "package_registry_fingerprint": MODULE_PORT_SCAN_FINGERPRINT,
            "defines": list(defines) if defines is not None else None,
        }
        payload = store.load_cached_worker_result(**key) if store is not None and use_cache else None
        if payload is not None and isinstance(payload.get("module_ports"), dict):
            ports_by_module = {
                name: [(port, direction) for port, direction in ports]
                for name, ports in payload["module_ports"].items()
            }
            children = [str(name) for name in payload.get("instantiated", [])]
        else:
            tree = call_parse_file(_parse_file, str(path), include_dirs=include_dirs, defines=defines)
            if extract_parse_diagnostics(tree, str(path)):
                continue
            ports_by_module = module_ports_in_file(tree)
            children = instantiated_module_names(tree)
            if store is not None:
                try:
                    store.store_cached_worker_result(
                        worker_result={
                            "module_ports": {n: [list(p) for p in ps] for n, ps in ports_by_module.items()},
                            "instantiated": children,
                        },
                        header_dependencies=extract_header_dependencies(tree),
                        **key,
                    )
                except sqlite3.Error as exc:
                    warn_store_unavailable(store.path, exc)
        record_module_ports(str(path), ports_by_module, registry)
        children_by_path[str(path)] = children
    return registry, children_by_path


def scan_module_ports_from_trees(file_inputs: Sequence[tuple[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    registry: dict[str, list[dict[str, Any]]] = {}
    for file_name, tree in file_inputs:
        record_module_ports(file_name, module_ports_in_file(tree), registry)
    return registry


def file_fingerprint(
    package_registry: dict[str, list[dict[str, Any]]] | None,
    module_ports: dict[str, list[dict[str, Any]]] | None,
    instantiated: list[str],
) -> str | None:
    """The cache-key fingerprint of what a file's walk reads from the other files: every package, and the
    ports of the modules the file instantiates."""
    packages = fingerprint_package_registry(package_registry) if package_registry else None
    ports = fingerprint_module_ports({name: module_ports[name] for name in instantiated if name in (module_ports or {})})
    if packages is None and ports is None:
        return None
    return json.dumps([packages, ports])
