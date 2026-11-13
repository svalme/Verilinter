from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence

from .analysis_store import AnalysisStore, file_sha256
from .diagnostics import enrich_diagnostics, filter_by_baseline, sort_diagnostics
from .parser.parse import (
    extract_header_dependencies,
    extract_parse_diagnostics,
    file_uses_default_nettype_none,
    parse_file,
    tree_has_package_declaration,
)
from .parser.syntax import instantiated_module_names, module_ports_in_file
from .parser.traversal_guard import collect_truncations
from .rules.register_rules import *
from .rules.register_rules import module_rule_runner, rule_runner, symbol_rule_runner
from .rules.rule_selection import RuleSelection
from .semantic.models import InstanceRecord
from .semantic.scope import Scope
from .semantic.connection_records import resolve_connections
from .semantic.instance_effects import apply_instance_port_effects
from .store.keys import MODULE_PORT_SCAN_FINGERPRINT
from .semantic.module_registry import (
    fingerprint_module_ports,
    record_module_ports,
    seed_cross_file_module_ports,
)
from .semantic.package_registry import (
    fingerprint_package_registry,
    record_packages_from_symbol_table,
    seed_cross_file_packages,
)
from .semantic.symbol_serialization import symbol_from_dict, symbol_to_dict
from .semantic.symbol_table import SymbolTable
from .walk.context import Context
from .walk.dispatch import dispatch
from .walk.walker import Walker
from .handlers.register_handlers import *
from .vnodes.register_vnodes import *

import inspect
import sys
from .semantic.scope_kinds import ScopeKind


def _get_override(attr: str, default: Any) -> Any:
    rl = sys.modules.get("src.run_lint")
    if rl is not None and hasattr(rl, attr):
        return getattr(rl, attr)
    return default


def _call_parse_file(
    parse_fn: Any,
    path: str,
    include_dirs: list[str] | None = None,
    defines: Sequence[str] | None = None,
) -> Any:
    try:
        sig = inspect.signature(parse_fn)
        params = sig.parameters
        accepts_defines = "defines" in params or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        accepts_include_dirs = "include_dirs" in params or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    except (ValueError, TypeError):
        accepts_defines = True
        accepts_include_dirs = True

    kwargs: dict[str, Any] = {}
    if accepts_include_dirs:
        kwargs["include_dirs"] = include_dirs
    if accepts_defines and defines is not None:
        kwargs["defines"] = defines
    elif accepts_defines:
        kwargs["defines"] = defines

    return parse_fn(path, **kwargs)


@dataclass(frozen=True)
class WorkerResult:
    diagnostics: list[dict[str, Any]]
    modules: list[dict[str, Any]]
    primitives: list[str]
    module_references: list[tuple[str, dict[str, Any]]]
    instantiation_edges: list[tuple[str, str, dict[str, Any]]]
    instantiations: list[InstanceRecord]
    header_dependencies: list[dict[str, str]] = field(default_factory=list)
    truncations: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class AnalysisResult:
    diagnostics: list[dict[str, Any]]
    symbol_table: SymbolTable
    cache_stats: dict[str, int] | None = None
    truncations: list[dict[str, Any]] = field(default_factory=list)
    suppressed_by_baseline: int = 0


def collect_paths(raw: list[str], exclude: list[str] | None = None) -> list[Path]:
    """Discover `.v`/`.sv` files from a mix of directory and file arguments,
    dropping duplicates and, when `exclude` is given, any candidate matching
    one of those glob patterns.

    Patterns match via `PurePath.match`, which matches from the right end of
    the path -- a single-component pattern (`*_tb.v`) matches any file with
    that name regardless of directory, and a multi-component one
    (`dhrystone/*`) matches anything under a directory with that name,
    without needing a wildcard on both sides. Applied uniformly to both
    directory-discovered files and explicitly named file arguments, so
    behavior doesn't depend on which form a given path arrived in.
    """
    exclude_patterns = exclude or []
    paths: list[Path] = []
    seen: set[Path] = set()
    for r in raw:
        p = Path(r)
        if p.is_dir():
            candidates = [*sorted(p.rglob("*.v")), *sorted(p.rglob("*.sv"))]
        else:
            candidates = [p]

        for candidate in candidates:
            if any(candidate.match(pattern) for pattern in exclude_patterns):
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append(candidate)
    return paths


def _build_rule_selection(
    rule_selection: RuleSelection | None,
    rule_profile: str | None,
) -> RuleSelection | None:
    if rule_selection is not None and rule_profile is not None:
        raise ValueError("pass either rule_selection or rule_profile, not both")

    if rule_selection is not None:
        return rule_selection

    if rule_profile is None or rule_profile == "all":
        return None

    return RuleSelection(enabled_profiles=frozenset({rule_profile}))


def _file_may_declare_package(path: Path) -> bool:
    """Non-regex lexical prefilter so `_scan_packages` avoids parsing files
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


def _scan_packages(
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
        _Walker = _get_override("Walker", Walker)
        _parse_file = _get_override("parse_file", parse_file)
        _file_uses_default_nettype_none = _get_override("file_uses_default_nettype_none", file_uses_default_nettype_none)
        tree = _call_parse_file(_parse_file, str(path), include_dirs=include_dirs, defines=defines)
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


def _scan_packages_from_trees(
    file_inputs: Sequence[tuple[str, Any]],
    default_nettype_none_by_file: dict[str, bool] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    registry: dict[str, list[dict[str, Any]]] = {}
    _Walker = _get_override("Walker", Walker)
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


def _scan_module_ports(
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
    _parse_file = _get_override("parse_file", parse_file)
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
            tree = _call_parse_file(_parse_file, str(path), include_dirs=include_dirs, defines=defines)
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
                    _warn_store_unavailable(store.path, exc)
        record_module_ports(str(path), ports_by_module, registry)
        children_by_path[str(path)] = children
    return registry, children_by_path


def _scan_module_ports_from_trees(file_inputs: Sequence[tuple[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    registry: dict[str, list[dict[str, Any]]] = {}
    for file_name, tree in file_inputs:
        record_module_ports(file_name, module_ports_in_file(tree), registry)
    return registry


def _file_fingerprint(
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


def _lint_single_tree(
    file_name: str,
    tree: Any,
    rule_selection: RuleSelection | None = None,
    package_registry: dict[str, list[dict[str, Any]]] | None = None,
    default_nettype_none: bool = False,
    header_dependencies: list[dict[str, str]] | None = None,
    rule_runner_inst: Any = None,
    symbol_rule_runner_inst: Any = None,
    module_ports: dict[str, list[dict[str, Any]]] | None = None,
) -> WorkerResult:
    _Walker = _get_override("Walker", Walker)
    _rule_runner = rule_runner_inst or _get_override("rule_runner", rule_runner)
    _symbol_rule_runner = symbol_rule_runner_inst or _get_override(
        "symbol_rule_runner", symbol_rule_runner
    )

    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = _Walker(dispatch)
    ast_diagnostics: list[dict[str, Any]] = []

    def on_node(vnode: object, node_ctx: object) -> None:
        ast_diagnostics.extend(_rule_runner.check(vnode, node_ctx, rule_selection))

    symbol_table.set_current_file(file_name)
    symbol_table.set_current_file_default_nettype_none(default_nettype_none)
    seed_cross_file_packages(symbol_table, package_registry, file_name)
    seed_cross_file_module_ports(symbol_table, module_ports, file_name)

    truncations: list[dict[str, Any]] = []
    with collect_truncations(file_name=file_name, tree=tree) as trunc_events:
        walker.walk(tree.root, tree, ctx, symbol_table, on_node=on_node)
        apply_instance_port_effects(symbol_table)
        diagnostics = ast_diagnostics + _symbol_rule_runner.run(symbol_table, rule_selection)
        truncations = [e.to_dict() for e in trunc_events]

    modules: list[dict[str, Any]] = []
    for name, scopes in symbol_table.modules.items():
        for scope in scopes:
            symbols: list[dict[str, object]] = []
            for symbol in scope.symbols.values():
                symbols.append(symbol_to_dict(symbol))
            modules.append(
                {
                    "name": name,
                    "file": scope.file,
                    "location": scope.location,
                    "symbols": symbols,
                }
            )

    return WorkerResult(
        diagnostics=diagnostics,
        modules=modules,
        primitives=sorted(symbol_table.primitives),
        module_references=list(symbol_table.module_references),
        instantiation_edges=list(symbol_table.instantiation_edges),
        instantiations=list(symbol_table.instantiations),
        header_dependencies=header_dependencies or [],
        truncations=truncations,
    )


def _lint_single_file(
    path: str,
    rule_selection: RuleSelection | None,
    include_dirs: list[str] | None = None,
    package_registry: dict[str, list[dict[str, Any]]] | None = None,
    defines: Sequence[str] | None = None,
    rule_runner_inst: Any = None,
    symbol_rule_runner_inst: Any = None,
    module_ports: dict[str, list[dict[str, Any]]] | None = None,
) -> WorkerResult:
    _parse_file = _get_override("parse_file", parse_file)
    _file_uses_default_nettype_none = _get_override(
        "file_uses_default_nettype_none", file_uses_default_nettype_none
    )

    tree = _call_parse_file(_parse_file, path, include_dirs=include_dirs, defines=defines)
    header_dependencies = extract_header_dependencies(tree)
    parse_errors = extract_parse_diagnostics(tree, path)
    if parse_errors:
        return WorkerResult(
            diagnostics=parse_errors,
            modules=[],
            primitives=[],
            module_references=[],
            instantiation_edges=[],
            instantiations=[],
            header_dependencies=header_dependencies,
        )

    return _lint_single_tree(
        file_name=path,
        tree=tree,
        rule_selection=rule_selection,
        package_registry=package_registry,
        default_nettype_none=_file_uses_default_nettype_none(path),
        header_dependencies=header_dependencies,
        rule_runner_inst=rule_runner_inst,
        symbol_rule_runner_inst=symbol_rule_runner_inst,
        module_ports=module_ports,
    )


def _build_cross_file_symbol_table(results: list[WorkerResult]) -> SymbolTable:
    symbol_table = SymbolTable()

    for result in results:
        for module in result.modules:
            location = dict(module["location"])
            if module.get("file"):
                location["file"] = module["file"]
            scope = Scope(kind=ScopeKind.MODULE, name=module["name"], location=location)
            scope.file = module.get("file")
            for symbol_data in module.get("symbols", []):
                symbol = symbol_from_dict(symbol_data)
                scope.define(symbol)
            symbol_table.modules.setdefault(module["name"], []).append(scope)

        symbol_table.primitives.update(result.primitives)
        symbol_table.module_references.extend(result.module_references)
        symbol_table.instantiation_edges.extend(result.instantiation_edges)
        symbol_table.instantiations.extend(result.instantiations)

    resolve_connections(symbol_table)
    return symbol_table


def _run_workers(
    paths: list[Path],
    jobs: int,
    rule_selection: RuleSelection | None,
    include_dirs: list[str] | None = None,
    package_registry: dict[str, list[dict[str, Any]]] | None = None,
    defines: Sequence[str] | None = None,
    rule_runner_inst: Any = None,
    symbol_rule_runner_inst: Any = None,
    module_ports: dict[str, list[dict[str, Any]]] | None = None,
) -> list[WorkerResult]:
    ordered_paths = [str(path) for path in paths]

    if jobs == 1 or rule_runner_inst is not None or symbol_rule_runner_inst is not None:
        return [
            _lint_single_file(
                path,
                rule_selection,
                include_dirs,
                package_registry,
                defines,
                rule_runner_inst=rule_runner_inst,
                symbol_rule_runner_inst=symbol_rule_runner_inst,
                module_ports=module_ports,
            )
            for path in ordered_paths
        ]

    try:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            return list(
                pool.map(
                    _lint_single_file,
                    ordered_paths,
                    [rule_selection] * len(ordered_paths),
                    [include_dirs] * len(ordered_paths),
                    [package_registry] * len(ordered_paths),
                    [defines] * len(ordered_paths),
                    [None] * len(ordered_paths),
                    [None] * len(ordered_paths),
                    [module_ports] * len(ordered_paths),
                )
            )
    except (OSError, PermissionError):
        return [
            _lint_single_file(path, rule_selection, include_dirs, package_registry, defines, module_ports=module_ports)
            for path in ordered_paths
        ]


def _worker_result_from_payload(payload: dict[str, Any]) -> WorkerResult:
    return WorkerResult(
        diagnostics=list(payload.get("diagnostics", [])),
        modules=list(payload.get("modules", [])),
        primitives=list(payload.get("primitives", [])),
        module_references=list(payload.get("module_references", [])),
        instantiation_edges=list(payload.get("instantiation_edges", [])),
        instantiations=[
            InstanceRecord.from_dict(inst) if isinstance(inst, dict) else inst
            for inst in payload.get("instantiations", [])
        ],
        header_dependencies=list(payload.get("header_dependencies", [])),
        truncations=list(payload.get("truncations", [])),
    )


def _warn_store_unavailable(store_path: Path, exc: Exception) -> None:
    print(
        f"warning: analysis store {store_path} is unusable ({exc}); continuing without the cache",
        file=sys.stderr,
    )


def run(
    paths: list[Path],
    jobs: int = 1,
    rule_selection: RuleSelection | None = None,
    rule_profile: str | None = None,
    severity_overrides: dict[str, str] | None = None,
    baseline_path: Path | None = None,
    include_dirs: list[str] | None = None,
    defines: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    return analyze(
        paths,
        jobs=jobs,
        rule_selection=rule_selection,
        rule_profile=rule_profile,
        severity_overrides=severity_overrides,
        baseline_path=baseline_path,
        include_dirs=include_dirs,
        defines=defines,
    ).diagnostics


class LintPipeline:
    """Unified multi-phase analysis pipeline shared between production and test harnesses.

    Executes identical analysis phases:
    1. Scan package declarations across all inputs to build package_registry.
    2. Execute isolated per-file workers (each with its own SymbolTable).
    3. Validate serialization / deserialization boundary of WorkerResult payloads.
    4. Aggregate cross-file SymbolTable from WorkerResult records.
    5. Execute cross-file module rules (ModuleRuleRunner) on the aggregated SymbolTable.
    6. Aggregate, enrich, and sort diagnostics.
    """

    def __init__(
        self,
        rule_runner: Any = None,
        symbol_rule_runner: Any = None,
        module_rule_runner: Any = None,
        store: Any = None,
    ) -> None:
        self._rule_runner = rule_runner
        self._symbol_rule_runner = symbol_rule_runner
        self._module_rule_runner = module_rule_runner
        self._store = store

    def analyze_trees(
        self,
        file_inputs: Sequence[tuple[str, Any]],
        *,
        default_nettype_none_by_file: dict[str, bool] | None = None,
        allow_parse_errors: bool = False,
        selection: RuleSelection | None = None,
        jobs: int = 1,
    ) -> AnalysisResult:
        if jobs != 1:
            raise NotImplementedError("In-memory tree linting only supports sequential execution")

        if not allow_parse_errors:
            for file_name, tree in file_inputs:
                errs = extract_parse_diagnostics(tree, file_name)
                if errs:
                    formatted = [f"{e['line']}:{e['col']}: {e['message']}" for e in errs]
                    raise AssertionError(
                        f"Unexpected parser errors in {file_name}:\n  " + "\n  ".join(formatted)
                    )

        # Phase 1: Scan packages across all input trees
        package_registry = _scan_packages_from_trees(
            file_inputs, default_nettype_none_by_file=default_nettype_none_by_file
        )

        module_ports = _scan_module_ports_from_trees(file_inputs)

        # Phase 2: Isolated per-file worker linting
        worker_results: list[WorkerResult] = []
        for file_name, tree in file_inputs:
            parse_errors = extract_parse_diagnostics(tree, file_name)
            if parse_errors and not allow_parse_errors:
                res = WorkerResult(
                    diagnostics=parse_errors,
                    modules=[],
                    primitives=[],
                    module_references=[],
                    instantiation_edges=[],
                    instantiations=[],
                    header_dependencies=[],
                )
            else:
                res = _lint_single_tree(
                    file_name=file_name,
                    tree=tree,
                    rule_selection=selection,
                    package_registry=package_registry,
                    default_nettype_none=(default_nettype_none_by_file or {}).get(file_name, False),
                    rule_runner_inst=self._rule_runner,
                    symbol_rule_runner_inst=self._symbol_rule_runner,
                    module_ports=module_ports,
                )
                if parse_errors and allow_parse_errors:
                    res = WorkerResult(
                        diagnostics=parse_errors + res.diagnostics,
                        modules=res.modules,
                        primitives=res.primitives,
                        module_references=res.module_references,
                        instantiation_edges=res.instantiation_edges,
                        instantiations=res.instantiations,
                        header_dependencies=res.header_dependencies,
                    )

            # Phase 3: Serialization / Deserialization boundary round-trip
            payload = asdict(res)
            res = _worker_result_from_payload(payload)
            worker_results.append(res)

        # Phase 4: Cross-file symbol table aggregation
        cross_file_symbol_table = _build_cross_file_symbol_table(worker_results)

        # Phase 5: Cross-file module rules
        _mod_runner = self._module_rule_runner or _get_override("module_rule_runner", module_rule_runner)
        module_diagnostics = _mod_runner.run(cross_file_symbol_table, selection)

        # Phase 6: Diagnostics aggregation
        diagnostics: list[dict[str, Any]] = []
        truncations: list[dict[str, Any]] = []
        for w_res in worker_results:
            diagnostics.extend(w_res.diagnostics)
            truncations.extend(w_res.truncations)
        diagnostics.extend(module_diagnostics)
        diagnostics = sort_diagnostics(diagnostics)

        return AnalysisResult(
            diagnostics=diagnostics,
            symbol_table=cross_file_symbol_table,
            truncations=truncations,
        )

    def analyze_paths(
        self,
        paths: list[Path],
        jobs: int = 1,
        rule_selection: RuleSelection | None = None,
        rule_profile: str | None = None,
        severity_overrides: dict[str, str] | None = None,
        baseline_path: Path | None = None,
        store_path: Path | None = None,
        use_cache: bool = True,
        fmt: str = "text",
        report_kind: str | None = None,
        include_dirs: list[str] | None = None,
        defines: Sequence[str] | None = None,
    ) -> AnalysisResult:
        if jobs < 1:
            raise ValueError(f"jobs must be >= 1, got {jobs}")

        resolved_selection = _build_rule_selection(rule_selection, rule_profile)
        normalized_defines = [str(d) for d in defines] if defines is not None else None

        for path in paths:
            if not path.exists():
                raise FileNotFoundError(f"file not found: {path}")

        package_registry = _scan_packages(paths, include_dirs, defines=normalized_defines)

        store = self._store
        if store is None and store_path is not None:
            try:
                store = AnalysisStore(store_path)
            except sqlite3.Error as exc:
                _warn_store_unavailable(store_path, exc)
        module_ports, instantiated_by_path = _scan_module_ports(
            paths, include_dirs, defines=normalized_defines, store=store, use_cache=use_cache
        )

        def file_fingerprint(path: Path) -> str | None:
            return _file_fingerprint(package_registry, module_ports, instantiated_by_path.get(str(path), []))

        file_records: list[dict[str, Any]] = []
        results_by_path: dict[str, WorkerResult] = {}
        missed_paths: list[Path] = []
        cache_hits = 0

        if store is not None:
            for path in paths:
                file_hash = file_sha256(path)
                payload = (
                    store.load_cached_worker_result(
                        file_path=str(path),
                        file_hash=file_hash,
                        rule_selection=resolved_selection,
                        include_dirs=include_dirs,
                        package_registry_fingerprint=file_fingerprint(path),
                        defines=normalized_defines,
                    )
                    if use_cache
                    else None
                )
                cached_result: WorkerResult | None = None
                if payload is not None:
                    try:
                        cached_result = _worker_result_from_payload(payload)
                    except (KeyError, TypeError, ValueError, AttributeError):
                        cached_result = None
                if cached_result is not None:
                    results_by_path[str(path)] = cached_result
                    cache_hits += 1
                    file_records.append(
                        {"file_path": str(path), "file_hash": file_hash, "cache_hit": True}
                    )
                else:
                    missed_paths.append(path)
                    file_records.append(
                        {"file_path": str(path), "file_hash": file_hash, "cache_hit": False}
                    )
        else:
            missed_paths = list(paths)

        fresh_results = (
            _run_workers(
                missed_paths,
                jobs,
                resolved_selection,
                include_dirs,
                package_registry,
                defines=normalized_defines,
                rule_runner_inst=self._rule_runner,
                symbol_rule_runner_inst=self._symbol_rule_runner,
                module_ports=module_ports,
            )
            if missed_paths
            else []
        )
        for path, result in zip(missed_paths, fresh_results):
            results_by_path[str(path)] = result
            if store is not None:
                try:
                    store.store_cached_worker_result(
                        file_path=str(path),
                        file_hash=file_sha256(path),
                        rule_selection=resolved_selection,
                        worker_result=asdict(result),
                        include_dirs=include_dirs,
                        package_registry_fingerprint=file_fingerprint(path),
                        defines=normalized_defines,
                        header_dependencies=result.header_dependencies,
                    )
                except sqlite3.Error as exc:
                    _warn_store_unavailable(store.path, exc)
                    store = None

        results = [results_by_path[str(path)] for path in paths]
        diagnostics: list[dict[str, Any]] = []
        truncations: list[dict[str, Any]] = []
        for result in results:
            diagnostics.extend(result.diagnostics)
            truncations.extend(result.truncations)

        cross_file_symbol_table = _build_cross_file_symbol_table(results)
        _mod_runner = self._module_rule_runner or _get_override("module_rule_runner", module_rule_runner)
        diagnostics.extend(_mod_runner.run(cross_file_symbol_table, resolved_selection))
        diagnostics = enrich_diagnostics(diagnostics, severity_overrides)
        diagnostics = sort_diagnostics(diagnostics)
        reported_count = len(diagnostics)
        diagnostics = filter_by_baseline(diagnostics, baseline_path)
        suppressed_by_baseline = reported_count - len(diagnostics)
        if store is not None:
            try:
                store.record_run(
                    cwd=str(Path.cwd()),
                    fmt=fmt,
                    report_kind=report_kind,
                    jobs=jobs,
                    rule_selection=resolved_selection,
                    baseline_path=str(baseline_path) if baseline_path is not None else None,
                    file_records=file_records,
                    diagnostics=diagnostics,
                    symbol_table=cross_file_symbol_table,
                )
            except sqlite3.Error as exc:
                _warn_store_unavailable(store.path, exc)
                store = None
        return AnalysisResult(
            diagnostics=diagnostics,
            symbol_table=cross_file_symbol_table,
            cache_stats={"hits": cache_hits, "misses": len(paths) - cache_hits}
            if store is not None
            else None,
            truncations=truncations,
            suppressed_by_baseline=suppressed_by_baseline,
        )


def analyze(
    paths: list[Path],
    jobs: int = 1,
    rule_selection: RuleSelection | None = None,
    rule_profile: str | None = None,
    severity_overrides: dict[str, str] | None = None,
    baseline_path: Path | None = None,
    store_path: Path | None = None,
    use_cache: bool = True,
    fmt: str = "text",
    report_kind: str | None = None,
    include_dirs: list[str] | None = None,
    defines: Sequence[str] | None = None,
) -> AnalysisResult:
    return LintPipeline().analyze_paths(
        paths=paths,
        jobs=jobs,
        rule_selection=rule_selection,
        rule_profile=rule_profile,
        severity_overrides=severity_overrides,
        baseline_path=baseline_path,
        store_path=store_path,
        use_cache=use_cache,
        fmt=fmt,
        report_kind=report_kind,
        include_dirs=include_dirs,
        defines=defines,
    )
