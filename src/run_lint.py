import argparse
import sys
from pathlib import Path

import pyslang as sl

from pkg.ast.walker import Walker
from pkg.ast.context import Context
from pkg.ast.symbol_table import SymbolTable
from pkg.ast.dispatch import dispatch
from pkg.vnode.syntax_vnode import SyntaxVNode
from pkg.handlers.register_handlers import *
from pkg.rules.register_rules import *


def run_file(path):
    
    # Parse source
    tree = sl.SyntaxTree.fromFile(str(path))
    root = SyntaxVNode(tree.root, tree)

    # Initialize symbol table and context
    symbol_table = SymbolTable()
    global_scope = symbol_table.new_scope(kind="global", name="global")
    ctx = Context(scopes=[global_scope])

    # Walk AST
    dispatch.set_default(SyntaxNodeHandler())
    walker = Walker(dispatch)
    walker.walk(root, ctx, symbol_table)

    # Run rules
    ast_diagnostics = rule_runner.run(walker._results) # AST-based rules
    symbol_diagnostics = symbol_rule_runner.run(symbol_table) # Symbol-based rules
    diagnostics = ast_diagnostics + symbol_diagnostics

    # Output
    if not diagnostics:
        print("No issues found.")
    else:
        for d in diagnostics:
            print(f"{d['line']}:{d['col']} — {d['message']}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Verilog static analyzer")
    parser.add_argument("file", help="Verilog source file")
    args = parser.parse_args()

    if len(sys.argv) != 2:
        print("Usage: python run_lint.py <file.v>")
        sys.exit(1)

    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}")
        sys.exit(1)

    run_file(path)
