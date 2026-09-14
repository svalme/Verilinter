from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pkg.analysis_store import AnalysisStore, file_sha256
from pkg.config import LintConfig, config_from_cli, find_default_config, load_config, merge_config
from pkg.diagnostics import enrich_diagnostics, filter_by_baseline, sort_diagnostics, write_baseline
from pkg.output import render_connection_report, render_diagnostics
from pkg.parser.parse import (
    extract_parse_diagnostics,
    file_uses_default_nettype_none,
    parse_file,
)
from pkg.rules.profiles import available_rule_profiles
from pkg.rules.register_rules import *
from pkg.rules.register_rules import module_rule_runner, rule_runner, symbol_rule_runner
from pkg.rules.rule_selection import RuleSelection
from pkg.semantic.scope import Scope
from pkg.semantic.symbol import Symbol
from pkg.semantic.symbol_table import SymbolTable
from pkg.walk.context import Context
from pkg.walk.dispatch import dispatch
from pkg.walk.walker import Walker
from pkg.handlers.register_handlers import *
from pkg.vnodes.register_vnodes import *


@dataclass(frozen=True)
class WorkerResult:
    diagnostics: list[dict[str, Any]]
    modules: list[dict[str, Any]]
    primitives: list[str]
    module_references: list[tuple[str, dict[str, Any]]]
    instantiation_edges: list[tuple[str, str, dict[str, Any]]]
    instantiations: list[dict[str, object]]


@dataclass(frozen=True)
class AnalysisResult:
    diagnostics: list[dict[str, Any]]
    symbol_table: SymbolTable
    cache_stats: dict[str, int] | None = None


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


_PACKAGE_KEYWORD_RE = re.compile(r"\bpackage\b")


def _file_may_declare_package(path: Path) -> bool:
    """Cheap text prefilter so `_scan_packages` doesn't have to fully parse
    every input file just to learn that most of them declare no package."""
    try:
        text = path.read_text(errors="ignore")
    except OSError:
        return False
    return _PACKAGE_KEYWORD_RE.search(text) is not None


def _scan_packages(
    paths: list[Path], include_dirs: list[str] | None = None
) -> dict[str, list[dict[str, Any]]]:
    """First pass over the corpus: find every `package ... endpackage`
    declaration and what it exports, before any per-file lint worker runs.

    NO_IMPLICIT_NET and friends resolve a package-qualified/wildcard-imported
    name during each file's OWN single-file walk (see identifier_name_handler.py),
    so package visibility has to be known before that walk starts -- unlike
    UNDEFINED_MODULE/DUPLICATE_MODULE, which reconcile module definitions
    across files only after every worker finishes (see
    `_build_cross_file_symbol_table`). Filtered through
    `_file_may_declare_package` so a codebase with few or no packages doesn't
    pay for a second full-corpus parse+walk.
    """
    registry: dict[str, list[dict[str, Any]]] = {}
    for path in paths:
        if not _file_may_declare_package(path):
            continue
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)
        symbol_table.set_current_file(str(path))
        symbol_table.set_current_file_default_nettype_none(file_uses_default_nettype_none(path))
        tree = parse_file(str(path), include_dirs=include_dirs)
        if extract_parse_diagnostics(tree, str(path)):
            continue
        walker.walk(tree.root, tree, ctx, symbol_table)
        for name, scopes in symbol_table.packages.items():
            for scope in scopes:
                symbols = [
                    {"name": symbol.name, "kind": symbol.kind}
                    for symbol in scope.symbols.values()
                    if symbol.is_declared and not symbol.is_implicit
                ]
                registry.setdefault(name, []).append({"file": str(path), "symbols": symbols})
    return registry


def _fingerprint_package_registry(registry: dict[str, list[dict[str, Any]]]) -> str | None:
    """Stable fingerprint of `_scan_packages`' output for the analysis-store cache
    key: a cached per-file result was resolved against a specific corpus-wide set
    of package declarations, and any of those changing (even in a different file)
    can change what a package-qualified/wildcard-imported name resolves to for
    the cached file -- see `_seed_cross_file_packages`."""
    if not registry:
        return None
    payload = {
        name: sorted(
            (entry["file"], tuple(sorted((s["name"], s["kind"]) for s in entry["symbols"])))
            for entry in entries
        )
        for name, entries in registry.items()
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _seed_cross_file_packages(
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
            scope = Scope(kind="package", name=name)
            scope.file = entry["file"]
            for symbol_data in entry["symbols"]:
                symbol = Symbol(name=str(symbol_data["name"]), kind=str(symbol_data.get("kind", "variable")))
                symbol.add_declaration({"line": 0, "col": 0, "file": entry["file"]})
                scope.define(symbol)
            symbol_table.packages.setdefault(name, []).append(scope)


def _lint_single_file(
    path: str,
    rule_selection: RuleSelection | None,
    include_dirs: list[str] | None = None,
    package_registry: dict[str, list[dict[str, Any]]] | None = None,
) -> WorkerResult:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)
    ast_diagnostics: list[dict[str, Any]] = []

    def on_node(vnode: object, node_ctx: object) -> None:
        ast_diagnostics.extend(rule_runner.check(vnode, node_ctx, rule_selection))

    symbol_table.set_current_file(path)
    symbol_table.set_current_file_default_nettype_none(file_uses_default_nettype_none(path))
    _seed_cross_file_packages(symbol_table, package_registry, path)
    tree = parse_file(path, include_dirs=include_dirs)
    parse_errors = extract_parse_diagnostics(tree, path)
    if parse_errors:
        return WorkerResult(
            diagnostics=parse_errors,
            modules=[],
            primitives=[],
            module_references=[],
            instantiation_edges=[],
            instantiations=[],
        )
    walker.walk(tree.root, tree, ctx, symbol_table, on_node=on_node)

    modules: list[dict[str, Any]] = []
    for name, scopes in symbol_table.modules.items():
        for scope in scopes:
            symbols: list[dict[str, object]] = []
            for symbol in scope.symbols.values():
                symbols.append(
                    {
                        "name": symbol.name,
                        "kind": symbol.kind,
                        "is_port": symbol.is_port,
                        "direction": symbol.port_direction,
                        "bit_width": symbol.bit_width,
                        "is_signed": symbol.is_signed,
                        "is_read": symbol.is_read,
                        "is_written": symbol.is_written,
                        "use_count": symbol.use_count,
                        "read_count": symbol.read_count,
                        "write_count": symbol.write_count,
                        # Lets a cross-file module rule (INSTANCE_OUTPUT_DRIVER_CONFLICT)
                        # tell a write confined to a `generate if`/`else` branch mutually
                        # exclusive with an instantiation's own branch from a genuine
                        # simultaneous conflict -- see branch_exclusivity_signature.
                        # `is_written`/counts above already summarize whether *any*
                        # write exists; this is the per-write detail that summary loses.
                        "write_branch_signatures": [
                            list(event.get("branch_signature", ()))
                            for event in symbol.use_events
                            if event["write"]
                        ],
                    }
                )
            modules.append(
                {
                    "name": name,
                    "file": scope.file,
                    "location": scope.location or {"line": 0, "col": 0},
                    "symbols": symbols,
                }
            )

    diagnostics = ast_diagnostics + symbol_rule_runner.run(symbol_table, rule_selection)
    return WorkerResult(
        diagnostics=diagnostics,
        modules=modules,
        primitives=sorted(symbol_table.primitives),
        module_references=list(symbol_table.module_references),
        instantiation_edges=list(symbol_table.instantiation_edges),
        instantiations=list(symbol_table.instantiations),
    )


def _build_cross_file_symbol_table(results: list[WorkerResult]) -> SymbolTable:
    symbol_table = SymbolTable()

    for result in results:
        for module in result.modules:
            location = dict(module["location"])
            if module.get("file") and "file" not in location:
                location["file"] = module["file"]
            scope = Scope(kind="module", name=module["name"], location=location)
            scope.file = module.get("file")
            for symbol_data in module.get("symbols", []):
                symbol = Symbol(name=str(symbol_data["name"]), kind=str(symbol_data.get("kind", "variable")))
                symbol.is_port = bool(symbol_data.get("is_port", False))
                symbol.port_direction = (
                    str(symbol_data.get("direction")) if symbol_data.get("direction") else None
                )
                symbol.bit_width = (
                    int(symbol_data["bit_width"]) if symbol_data.get("bit_width") is not None else None
                )
                signed = symbol_data.get("is_signed")
                symbol.is_signed = bool(signed) if signed is not None else None
                symbol.is_read = bool(symbol_data.get("is_read", False))
                symbol.is_written = bool(symbol_data.get("is_written", False))
                symbol.use_count = int(symbol_data.get("use_count", 0))
                symbol.read_count = int(symbol_data.get("read_count", 0))
                symbol.write_count = int(symbol_data.get("write_count", 0))
                # Reconstruct just enough of use_events for branch-exclusivity checks
                # (INSTANCE_OUTPUT_DRIVER_CONFLICT) to work on this cross-file table;
                # the summary fields above already cover every other consumer. Each
                # signature entry round-trips through the JSON-backed analysis store
                # as a plain list, so re-tuple it for use as a dict key.
                symbol.use_events = [
                    {
                        "location": {"line": 0, "col": 0},
                        "read": False,
                        "write": True,
                        "branch_signature": tuple(tuple(pair) for pair in raw_signature),
                    }
                    for raw_signature in symbol_data.get("write_branch_signatures", []) or []
                ]
                scope.define(symbol)
            symbol_table.modules.setdefault(module["name"], []).append(scope)

        symbol_table.primitives.update(result.primitives)
        symbol_table.module_references.extend(result.module_references)
        symbol_table.instantiation_edges.extend(result.instantiation_edges)
        symbol_table.instantiations.extend(result.instantiations)

    return symbol_table


def _run_workers(
    paths: list[Path],
    jobs: int,
    rule_selection: RuleSelection | None,
    include_dirs: list[str] | None = None,
    package_registry: dict[str, list[dict[str, Any]]] | None = None,
) -> list[WorkerResult]:
    ordered_paths = [str(path) for path in paths]

    if jobs == 1:
        return [
            _lint_single_file(path, rule_selection, include_dirs, package_registry)
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
                )
            )
    except (OSError, PermissionError):
        return [
            _lint_single_file(path, rule_selection, include_dirs, package_registry)
            for path in ordered_paths
        ]


def _worker_result_from_payload(payload: dict[str, Any]) -> WorkerResult:
    return WorkerResult(
        diagnostics=list(payload.get("diagnostics", [])),
        modules=list(payload.get("modules", [])),
        primitives=list(payload.get("primitives", [])),
        module_references=list(payload.get("module_references", [])),
        instantiation_edges=list(payload.get("instantiation_edges", [])),
        instantiations=list(payload.get("instantiations", [])),
    )


def run(
    paths: list[Path],
    jobs: int = 1,
    rule_selection: RuleSelection | None = None,
    rule_profile: str | None = None,
    severity_overrides: dict[str, str] | None = None,
    baseline_path: Path | None = None,
    include_dirs: list[str] | None = None,
) -> list[dict[str, Any]]:
    return analyze(
        paths,
        jobs=jobs,
        rule_selection=rule_selection,
        rule_profile=rule_profile,
        severity_overrides=severity_overrides,
        baseline_path=baseline_path,
        include_dirs=include_dirs,
    ).diagnostics


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
) -> AnalysisResult:
    if jobs < 1:
        raise ValueError(f"jobs must be >= 1, got {jobs}")

    resolved_selection = _build_rule_selection(rule_selection, rule_profile)

    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"file not found: {path}")

    # Must run before any cache lookup: a cached per-file result was resolved
    # against a specific corpus-wide set of package declarations (see
    # `_scan_packages`'s docstring), so the fingerprint below has to be part of
    # the cache key even on a full cache hit.
    package_registry = _scan_packages(paths, include_dirs)
    package_registry_fingerprint = _fingerprint_package_registry(package_registry)

    store = AnalysisStore(store_path) if store_path is not None else None
    file_records: list[dict[str, Any]] = []
    results_by_path: dict[str, WorkerResult] = {}
    missed_paths: list[Path] = []
    cache_hits = 0

    if store is not None:
        for path in paths:
            file_hash = file_sha256(path)
            # Until the store tracks transitive preprocessor dependencies, a
            # source containing directives must be reparsed: included headers
            # and macro-expanded includes can change without changing this file.
            cacheable = "`" not in path.read_text(errors="ignore")
            payload = (
                store.load_cached_worker_result(
                    file_path=str(path),
                    file_hash=file_hash,
                    rule_selection=resolved_selection,
                    include_dirs=include_dirs,
                    package_registry_fingerprint=package_registry_fingerprint,
                )
                if use_cache and cacheable
                else None
            )
            if payload is not None:
                results_by_path[str(path)] = _worker_result_from_payload(payload)
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
        _run_workers(missed_paths, jobs, resolved_selection, include_dirs, package_registry)
        if missed_paths
        else []
    )
    for path, result in zip(missed_paths, fresh_results):
        results_by_path[str(path)] = result
        if store is not None:
            store.store_cached_worker_result(
                file_path=str(path),
                file_hash=file_sha256(path),
                rule_selection=resolved_selection,
                worker_result=asdict(result),
                include_dirs=include_dirs,
                package_registry_fingerprint=package_registry_fingerprint,
            )

    results = [results_by_path[str(path)] for path in paths]
    diagnostics: list[dict[str, Any]] = []
    for result in results:
        diagnostics.extend(result.diagnostics)

    cross_file_symbol_table = _build_cross_file_symbol_table(results)
    diagnostics.extend(module_rule_runner.run(cross_file_symbol_table, resolved_selection))
    diagnostics = enrich_diagnostics(diagnostics, severity_overrides)
    diagnostics = sort_diagnostics(diagnostics)
    diagnostics = filter_by_baseline(diagnostics, baseline_path)
    if store is not None:
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
    return AnalysisResult(
        diagnostics=diagnostics,
        symbol_table=cross_file_symbol_table,
        cache_stats={"hits": cache_hits, "misses": len(paths) - cache_hits} if store is not None else None,
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="SystemVerilog static analyzer",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Verilog/SystemVerilog source files or directories (not required for --store maintenance flags)",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        metavar="PATTERN",
        help="skip files matching this glob pattern (matched from the right, "
        "e.g. '*_tb.v' or 'dhrystone/*'); repeat to exclude multiple",
    )
    parser.add_argument(
        "--include-dir",
        "-I",
        action="append",
        metavar="DIR",
        help="search this directory to resolve an `include compiler directive "
        "that references a header outside the source file's own directory "
        "(e.g. a vendored shared macro/assertion header); repeat for multiple",
    )
    parser.add_argument(
        "--jobs",
        "-j",
        type=int,
        default=None,
        metavar="N",
        help="number of worker processes to lint with",
    )
    parser.add_argument(
        "--profile",
        choices=available_rule_profiles(),
        help="built-in rule profile to enable",
    )
    parser.add_argument(
        "--rule",
        action="append",
        dest="rules",
        help="enable only the given rule code; repeat to allow multiple",
    )
    parser.add_argument(
        "--category",
        action="append",
        dest="categories",
        help="enable only the given rule category; repeat to allow multiple",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "sarif"),
        dest="fmt",
        default=None,
        help="render diagnostics as plain text, json, or sarif",
    )
    parser.add_argument(
        "--config",
        help="path to a .verilinter.toml configuration file",
    )
    parser.add_argument(
        "--severity",
        action="append",
        help="override severity for a rule, e.g. NO_SELF_ASSIGNMENT=error",
    )
    parser.add_argument(
        "--baseline",
        help="path to a JSON baseline file used to suppress known diagnostics",
    )
    parser.add_argument(
        "--write-baseline",
        help="write the current diagnostics to a baseline JSON file and exit",
    )
    parser.add_argument(
        "--report",
        choices=("connections",),
        help="print a structural report instead of diagnostics",
    )
    parser.add_argument(
        "--store",
        help="path to a local SQLite analysis store",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="disable reuse of cached per-file analysis results from the local store",
    )
    parser.add_argument(
        "--prune-cache-days",
        type=int,
        metavar="N",
        help="delete cached per-file results older than N days from --store, then exit",
    )
    parser.add_argument(
        "--prune-runs-keep",
        type=int,
        metavar="N",
        help="keep only the N most recently recorded runs in --store, deleting the rest, then exit",
    )
    parser.add_argument(
        "--vacuum-store",
        action="store_true",
        help="reclaim disk space in --store after pruning, then exit",
    )
    return parser.parse_args(argv)


def _resolve_config(args: argparse.Namespace) -> LintConfig:
    config = LintConfig()
    config_path: Path | None = None

    if args.config:
        config_path = Path(args.config).resolve()
    else:
        config_path = find_default_config()

    if config_path is not None:
        config = merge_config(config, load_config(config_path))

    cli_config = config_from_cli(
        profile=args.profile,
        rules=args.rules,
        categories=args.categories,
        fmt=args.fmt,
        jobs=args.jobs,
        severity=args.severity,
        baseline=args.baseline,
        store=args.store,
        no_cache=args.no_cache,
    )
    return merge_config(config, cli_config)


def _run_store_maintenance(args: argparse.Namespace) -> int:
    if not args.store:
        print("Error: --store is required for store maintenance flags", file=sys.stderr)
        return 1

    store = AnalysisStore(Path(args.store))
    if args.prune_cache_days is not None:
        removed = store.prune_cache(older_than_days=args.prune_cache_days)
        print(f"Pruned {removed} cached file result(s) older than {args.prune_cache_days} day(s).")
    if args.prune_runs_keep is not None:
        removed = store.prune_runs(keep_last=args.prune_runs_keep)
        print(f"Pruned {removed} run(s), keeping the {args.prune_runs_keep} most recent.")
    if args.vacuum_store:
        store.vacuum()
        print("Vacuumed store.")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    maintenance_requested = (
        args.prune_cache_days is not None or args.prune_runs_keep is not None or args.vacuum_store
    )
    if maintenance_requested:
        return _run_store_maintenance(args)

    try:
        config = _resolve_config(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    paths = collect_paths(args.paths, exclude=args.exclude)
    if not paths:
        print("Error: no .v or .sv files found", file=sys.stderr)
        return 1

    try:
        run_kwargs: dict[str, Any] = {"jobs": config.jobs}
        if config.to_rule_selection() is not None:
            run_kwargs["rule_selection"] = config.to_rule_selection()
        if config.severity_overrides:
            run_kwargs["severity_overrides"] = config.severity_overrides
        if config.baseline_path is not None:
            run_kwargs["baseline_path"] = config.baseline_path
        if config.store_path is not None:
            run_kwargs["store_path"] = config.store_path
            run_kwargs["use_cache"] = config.use_cache
        run_kwargs["fmt"] = config.fmt
        run_kwargs["report_kind"] = args.report
        if args.include_dir:
            run_kwargs["include_dirs"] = args.include_dir

        analysis = analyze(
            paths,
            **run_kwargs,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    has_parser_errors = any(d.get("code") == "PARSER_ERROR" for d in analysis.diagnostics)
    if args.write_baseline:
        if has_parser_errors:
            print("Error: cannot write baseline when files have parse errors", file=sys.stderr)
            return 1
        write_baseline(Path(args.write_baseline).resolve(), analysis.diagnostics)
        return 0

    if args.report == "connections":
        sys.stdout.write(render_connection_report(analysis.symbol_table))
        return 1 if has_parser_errors else 0

    sys.stdout.write(render_diagnostics(analysis.diagnostics, config.fmt))
    return 1 if has_parser_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
