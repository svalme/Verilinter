"""The analysis pipeline: pre-scans, workers, merge, module rules, aggregation."""
from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Sequence
from .analysis_store import AnalysisStore, file_sha256
from .store.keys import elaboration_keys
from .diagnostics import enrich_diagnostics, filter_by_baseline, sort_diagnostics
from .parser.elaborated_widths import ElaboratedWidths
from .parser.parse import extract_parse_diagnostics
from .rules.register_rules import *
from .rules.register_rules import module_rule_runner, rule_runner, symbol_rule_runner
from .rules.rule_selection import RuleSelection
from .semantic.scope import Scope
from .semantic.connection_records import resolve_connections
from .semantic.symbol_serialization import symbol_from_dict
from .semantic.symbol_table import SymbolTable
from .handlers.register_handlers import *
from .vnodes.register_vnodes import *
from .semantic.scope_kinds import ScopeKind
from .prescans import file_fingerprint, scan_module_ports, scan_module_ports_from_trees, scan_packages, scan_packages_from_trees
from .workers import WorkerResult, get_override, lint_single_tree, run_workers, warn_store_unavailable, worker_result_from_payload


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


def _build_cross_file_symbol_table(results: list[WorkerResult], widths: ElaboratedWidths | None = None) -> SymbolTable:
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

    resolve_connections(symbol_table, widths)
    return symbol_table


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


def _elaborated_widths(
    store: AnalysisStore | None,
    paths: list[Path],
    file_records: list[dict[str, Any]],
    results: list[WorkerResult],
    include_dirs: list[str] | None,
    defines: list[str] | None,
    use_cache: bool,
) -> ElaboratedWidths:
    """The elaborated widths of the file set: the stored record when no input changed, else built now and stored."""
    if store is None or len(file_records) != len(paths):
        return ElaboratedWidths.build(paths, include_dirs, defines)
    set_id, input_key = elaboration_keys(
        {record["file_path"]: record["file_hash"] for record in file_records},
        [dependency for result in results for dependency in result.header_dependencies],
        include_dirs,
        defines,
    )
    widths: ElaboratedWidths | None = None
    try:
        payload = store.load_cached_elaboration(set_id=set_id, input_key=input_key) if use_cache else None
        if payload is not None:
            try:
                return ElaboratedWidths.from_payload(payload)
            except ValueError:
                pass
        widths = ElaboratedWidths.build(paths, include_dirs, defines)
        store.store_cached_elaboration(set_id=set_id, input_key=input_key, payload=widths.to_payload())
    except sqlite3.Error as exc:
        warn_store_unavailable(store.path, exc)
    return widths if widths is not None else ElaboratedWidths.build(paths, include_dirs, defines)


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
        package_registry = scan_packages_from_trees(
            file_inputs, default_nettype_none_by_file=default_nettype_none_by_file
        )

        module_ports = scan_module_ports_from_trees(file_inputs)

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
                res = lint_single_tree(
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
            res = worker_result_from_payload(payload)
            worker_results.append(res)

        # Phase 4: Cross-file symbol table aggregation
        cross_file_symbol_table = _build_cross_file_symbol_table(worker_results)

        # Phase 5: Cross-file module rules
        _mod_runner = self._module_rule_runner or get_override("module_rule_runner", module_rule_runner)
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
        elaborated_widths: bool = False,
    ) -> AnalysisResult:
        if jobs < 1:
            raise ValueError(f"jobs must be >= 1, got {jobs}")

        resolved_selection = _build_rule_selection(rule_selection, rule_profile)
        normalized_defines = [str(d) for d in defines] if defines is not None else None

        for path in paths:
            if not path.exists():
                raise FileNotFoundError(f"file not found: {path}")

        package_registry = scan_packages(paths, include_dirs, defines=normalized_defines)

        store = self._store
        if store is None and store_path is not None:
            try:
                store = AnalysisStore(store_path)
            except sqlite3.Error as exc:
                warn_store_unavailable(store_path, exc)
        module_ports, instantiated_by_path = scan_module_ports(
            paths, include_dirs, defines=normalized_defines, store=store, use_cache=use_cache
        )

        def registry_fingerprint_for(path: Path) -> str | None:
            return file_fingerprint(package_registry, module_ports, instantiated_by_path.get(str(path), []))

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
                        package_registry_fingerprint=registry_fingerprint_for(path),
                        defines=normalized_defines,
                    )
                    if use_cache
                    else None
                )
                cached_result: WorkerResult | None = None
                if payload is not None:
                    try:
                        cached_result = worker_result_from_payload(payload)
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
            run_workers(
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
                        package_registry_fingerprint=registry_fingerprint_for(path),
                        defines=normalized_defines,
                        header_dependencies=result.header_dependencies,
                    )
                except sqlite3.Error as exc:
                    warn_store_unavailable(store.path, exc)
                    store = None

        results = [results_by_path[str(path)] for path in paths]
        diagnostics: list[dict[str, Any]] = []
        truncations: list[dict[str, Any]] = []
        for result in results:
            diagnostics.extend(result.diagnostics)
            truncations.extend(result.truncations)

        widths = (
            _elaborated_widths(store, paths, file_records, results, include_dirs, normalized_defines, use_cache)
            if elaborated_widths
            else None
        )
        cross_file_symbol_table = _build_cross_file_symbol_table(results, widths)
        _mod_runner = self._module_rule_runner or get_override("module_rule_runner", module_rule_runner)
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
                warn_store_unavailable(store.path, exc)
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
    elaborated_widths: bool = False,
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
        elaborated_widths=elaborated_widths,
    )
