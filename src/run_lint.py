import argparse
import sys
from pathlib import Path

import pyslang as sl

from pkg.walk.walker import Walker
from pkg.walk.context import Context
from pkg.semantic.symbol_table import SymbolTable
from pkg.walk.dispatch import dispatch
from pkg.vnodes.register_vnodes import *
from pkg.handlers.register_handlers import *
from pkg.rules.register_rules import *


def collect_paths(raw: list[str]) -> list[Path]:
    paths = []
    for r in raw:
        p = Path(r)
        if p.is_dir():
            paths.extend(sorted(p.rglob("*.v")))
            paths.extend(sorted(p.rglob("*.sv")))
        else:
            paths.append(p)
    return paths


def run(paths: list[Path], jobs: int = 1) -> list[dict]:
    if jobs < 1:
        raise ValueError(f"jobs must be >= 1, got {jobs}")
    if jobs > 1:
        raise NotImplementedError(
            "parallel linting (jobs > 1) is not implemented yet — "
            "see Docs/07_02_26/PARALLEL_LINTING_PLAN.md for the design and rollout plan"
        )

    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    ast_diagnostics: list[dict] = []

    def on_node(vnode, node_ctx) -> None:
        ast_diagnostics.extend(rule_runner.check(vnode, node_ctx))

    for path in paths:
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        symbol_table.set_current_file(str(path))
        tree = sl.SyntaxTree.fromFile(str(path))
        walker.walk(tree.root, tree, ctx, symbol_table, on_node=on_node)

    symbol_diagnostics = symbol_rule_runner.run(symbol_table)
    module_diagnostics = module_rule_runner.run(symbol_table)
    return ast_diagnostics + symbol_diagnostics + module_diagnostics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SystemVerilog static analyzer")
    parser.add_argument(
        "paths",
        nargs="+",
        help="Verilog/SystemVerilog source files or directories",
    )
    parser.add_argument(
        "--jobs", "-j",
        type=int,
        default=1,
        metavar="N",
        help="number of worker processes to lint with (default: 1, sequential; "
             "parallel execution with N > 1 is not implemented yet)",
    )
    args = parser.parse_args()

    paths = collect_paths(args.paths)
    if not paths:
        print("Error: no .v or .sv files found", file=sys.stderr)
        sys.exit(1)

    try:
        diagnostics = run(paths, jobs=args.jobs)
    except (ValueError, NotImplementedError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    if not diagnostics:
        print("No issues found.")
    else:
        for d in diagnostics:
            file_prefix = f"{d['file']}:" if d.get("file") else ""
            print(f"{file_prefix}{d['line']}:{d['col']} — {d['message']}")
