from __future__ import annotations

import argparse
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
from pkg.parser.parse import file_uses_default_nettype_none, parse_file
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


def collect_paths(raw: list[str]) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for r in raw:
        p = Path(r)
        if p.is_dir():
            candidates = [*sorted(p.rglob("*.v")), *sorted(p.rglob("*.sv"))]
        else:
            candidates = [p]

        for candidate in candidates:
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


def _lint_single_file(path: str, rule_selection: RuleSelection | None) -> WorkerResult:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)
    ast_diagnostics: list[dict[str, Any]] = []

    def on_node(vnode: object, node_ctx: object) -> None:
        ast_diagnostics.extend(rule_runner.check(vnode, node_ctx, rule_selection))

    symbol_table.set_current_file(path)
    symbol_table.set_current_file_default_nettype_none(file_uses_default_nettype_none(path))
    tree = parse_file(path)
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
) -> list[WorkerResult]:
    ordered_paths = [str(path) for path in paths]

    if jobs == 1:
        return [_lint_single_file(path, rule_selection) for path in ordered_paths]

    try:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            return list(pool.map(_lint_single_file, ordered_paths, [rule_selection] * len(ordered_paths)))
    except (OSError, PermissionError):
        return [_lint_single_file(path, rule_selection) for path in ordered_paths]


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
) -> list[dict[str, Any]]:
    return analyze(
        paths,
        jobs=jobs,
        rule_selection=rule_selection,
        rule_profile=rule_profile,
        severity_overrides=severity_overrides,
        baseline_path=baseline_path,
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
) -> AnalysisResult:
    if jobs < 1:
        raise ValueError(f"jobs must be >= 1, got {jobs}")

    resolved_selection = _build_rule_selection(rule_selection, rule_profile)

    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"file not found: {path}")

    store = AnalysisStore(store_path) if store_path is not None else None
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
                )
                if use_cache
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

    fresh_results = _run_workers(missed_paths, jobs, resolved_selection) if missed_paths else []
    for path, result in zip(missed_paths, fresh_results):
        results_by_path[str(path)] = result
        if store is not None:
            store.store_cached_worker_result(
                file_path=str(path),
                file_hash=file_sha256(path),
                rule_selection=resolved_selection,
                worker_result=asdict(result),
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
    parser = argparse.ArgumentParser(description="SystemVerilog static analyzer")
    parser.add_argument("paths", nargs="+", help="Verilog/SystemVerilog source files or directories")
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


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        config = _resolve_config(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    paths = collect_paths(args.paths)
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

        analysis = analyze(
            paths,
            **run_kwargs,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.write_baseline:
        write_baseline(Path(args.write_baseline).resolve(), analysis.diagnostics)
        return 0

    if args.report == "connections":
        sys.stdout.write(render_connection_report(analysis.symbol_table))
        return 0

    sys.stdout.write(render_diagnostics(analysis.diagnostics, config.fmt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
