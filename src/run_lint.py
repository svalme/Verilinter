from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pkg.analysis_store import AnalysisStore
from pkg.config import LintConfig, config_from_cli, find_default_config, load_config, merge_config
from pkg.diagnostics import write_baseline
from pkg.engine import (
    AnalysisResult,
    WorkerResult,
    analyze,
    collect_paths,
    run,
)
from pkg.output import render_connection_report, render_diagnostics
from pkg.parser.parse import extract_parse_diagnostics, file_uses_default_nettype_none, parse_file
from pkg.rules.profiles import available_rule_profiles
from pkg.rules.register_rules import module_rule_runner, rule_runner, symbol_rule_runner
from pkg.walk.walker import Walker

__all__ = [
    "AnalysisResult",
    "Walker",
    "WorkerResult",
    "analyze",
    "collect_paths",
    "extract_parse_diagnostics",
    "file_uses_default_nettype_none",
    "main",
    "module_rule_runner",
    "parse_file",
    "rule_runner",
    "run",
    "symbol_rule_runner",
]


def _build_lint_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verilinter",
        description="SystemVerilog static analyzer",
        fromfile_prefix_chars="@",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Verilog/SystemVerilog source files or directories",
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
        "-D",
        "--define",
        action="append",
        dest="defines",
        metavar="NAME[=VALUE]",
        help="define a preprocessor macro; repeat to allow multiple",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "sarif"),
        dest="fmt",
        default=None,
        help="render diagnostics as plain text, json, or sarif",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="write output directly to the specified file in UTF-8 instead of stdout",
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
        "--fail-on-error",
        action="store_true",
        help="exit with non-zero status code if any unsuppressed error-severity diagnostics exist",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="exit with non-zero status code if any unsuppressed warning- or error-severity diagnostics exist",
    )
    parser.add_argument(
        "--exit-zero",
        action="store_true",
        help="always exit with status code 0 unless an unhandled error occurs",
    )

    # Backward-compatible legacy store maintenance flags on top-level parser
    parser.add_argument(
        "--prune-cache-days",
        type=int,
        metavar="N",
        help="(Legacy) delete cached per-file results older than N days from --store, then exit",
    )
    parser.add_argument(
        "--prune-runs-keep",
        type=int,
        metavar="N",
        help="(Legacy) keep only the N most recently recorded runs in --store, deleting the rest, then exit",
    )
    parser.add_argument(
        "--vacuum-store",
        action="store_true",
        help="(Legacy) reclaim disk space in --store after pruning, then exit",
    )
    return parser


def _build_store_parser() -> argparse.ArgumentParser:
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "--store",
        help="path to the SQLite store database",
    )

    parser = argparse.ArgumentParser(
        prog="verilinter store",
        description="Manage the local SQLite analysis store",
        parents=[common_parser],
    )
    subparsers = parser.add_subparsers(dest="store_action", required=True)

    prune_parser = subparsers.add_parser(
        "prune",
        parents=[common_parser],
        help="prune cached file analysis records older than specified days",
    )
    prune_parser.add_argument(
        "--days",
        type=int,
        required=True,
        metavar="N",
        help="delete cache records older than N days",
    )

    runs_parser = subparsers.add_parser(
        "prune-runs",
        parents=[common_parser],
        help="prune historical run records, keeping only the most recent N",
    )
    runs_parser.add_argument(
        "--keep",
        type=int,
        required=True,
        metavar="N",
        help="number of recent runs to keep",
    )

    subparsers.add_parser("vacuum", parents=[common_parser], help="reclaim unused disk space in the store")
    subparsers.add_parser("status", parents=[common_parser], help="display store statistics and storage metrics")
    return parser


def _resolve_config(args: argparse.Namespace) -> LintConfig:
    config = LintConfig()
    config_path: Path | None = None

    if getattr(args, "config", None):
        config_path = Path(args.config).resolve()
    else:
        config_path = find_default_config()

    if config_path is not None:
        config = merge_config(config, load_config(config_path))

    cli_config = config_from_cli(
        profile=getattr(args, "profile", None),
        rules=getattr(args, "rules", None),
        categories=getattr(args, "categories", None),
        defines=getattr(args, "defines", None),
        fmt=getattr(args, "fmt", None),
        jobs=getattr(args, "jobs", None),
        severity=getattr(args, "severity", None),
        baseline=getattr(args, "baseline", None),
        store=getattr(args, "store", None),
        no_cache=getattr(args, "no_cache", False),
        output=getattr(args, "output", None),
        fail_on_error=getattr(args, "fail_on_error", False),
        fail_on_warning=getattr(args, "fail_on_warning", False),
        exit_zero=getattr(args, "exit_zero", False),
    )
    return merge_config(config, cli_config)


def _run_legacy_store_maintenance(args: argparse.Namespace) -> int:
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


def _run_store_subcommand(store_args: argparse.Namespace) -> int:
    store_path_str = store_args.store
    if not store_path_str:
        default_cfg = find_default_config()
        if default_cfg:
            cfg = load_config(default_cfg)
            if cfg.store_path:
                store_path_str = str(cfg.store_path)

    if not store_path_str:
        print("Error: --store path is required (or must be configured in .verilinter.toml)", file=sys.stderr)
        return 1

    store = AnalysisStore(Path(store_path_str))
    action = store_args.store_action

    if action == "prune":
        removed = store.prune_cache(older_than_days=store_args.days)
        print(f"Pruned {removed} cached file result(s) older than {store_args.days} day(s).")
    elif action == "prune-runs":
        removed = store.prune_runs(keep_last=store_args.keep)
        print(f"Pruned {removed} run(s), keeping the {store_args.keep} most recent.")
    elif action == "vacuum":
        store.vacuum()
        print("Vacuumed store.")
    elif action == "status":
        stats = store.status()
        print(json.dumps(stats, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)

    # Route subcommands if first token is "store" or "lint"
    if raw_args and raw_args[0] == "store":
        store_parser = _build_store_parser()
        parsed_store_args = store_parser.parse_args(raw_args[1:])
        return _run_store_subcommand(parsed_store_args)

    if raw_args and raw_args[0] == "lint":
        raw_args = raw_args[1:]

    lint_parser = _build_lint_parser()
    args = lint_parser.parse_args(raw_args)

    legacy_maintenance = (
        args.prune_cache_days is not None or args.prune_runs_keep is not None or args.vacuum_store
    )
    if legacy_maintenance:
        return _run_legacy_store_maintenance(args)

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
        if config.defines:
            run_kwargs["defines"] = config.defines

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
        rendered = render_connection_report(analysis.symbol_table)
    else:
        rendered = render_diagnostics(analysis.diagnostics, config.fmt)

    # Direct output to file or stdout
    if config.output_path:
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        config.output_path.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)

    # Compute exit code
    if config.exit_zero:
        return 0

    has_errors = has_parser_errors or any(d.get("severity") == "error" for d in analysis.diagnostics)
    has_warnings = has_errors or any(d.get("severity") == "warning" for d in analysis.diagnostics)

    if config.fail_on_warning and has_warnings:
        return 1
    if config.fail_on_error and has_errors:
        return 1

    return 1 if has_parser_errors else 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Legacy helper maintained for test suites."""
    return _build_lint_parser().parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
