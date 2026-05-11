import argparse
import sys
from pathlib import Path

import pyslang as sl

from pkg.ast.walker import Walker
from pkg.ast.context import Context
from pkg.ast.symbol_table import SymbolTable
from pkg.ast.dispatch import dispatch
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


def run(paths: list[Path]) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    for path in paths:
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        tree = sl.SyntaxTree.fromFile(str(path))
        walker.walk(tree.root, tree, ctx, symbol_table)

    ast_diagnostics = rule_runner.run(walker.results)
    symbol_diagnostics = symbol_rule_runner.run(symbol_table)
    return ast_diagnostics + symbol_diagnostics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SystemVerilog static analyzer")
    parser.add_argument(
        "paths",
        nargs="+",
        help="Verilog/SystemVerilog source files or directories",
    )
    args = parser.parse_args()

    paths = collect_paths(args.paths)
    if not paths:
        print("Error: no .v or .sv files found", file=sys.stderr)
        sys.exit(1)

    diagnostics = run(paths)
    if not diagnostics:
        print("No issues found.")
    else:
        for d in diagnostics:
            file_prefix = f"{d['file']}:" if d.get("file") else ""
            print(f"{file_prefix}{d['line']}:{d['col']} — {d['message']}")
