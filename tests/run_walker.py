import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

# handlers
from src.pkg.handlers.register_handlers import *

from src.pkg.rules.register_rules import *

import pyslang as sl

from src.pkg.vnode.syntax_vnode import SyntaxVNode
from src.pkg.ast.symbol_table import SymbolTable
from src.pkg.ast.context import Context
from src.pkg.ast.walker import Walker

from pathlib import Path
ROOT = Path(__file__).parent
path = ROOT / "data" / "simple.v"
tree = sl.SyntaxTree.fromFile(str(path))

root = SyntaxVNode(tree.root, tree)

from src.pkg.ast.dispatch import dispatch
dispatch.set_default(SyntaxNodeHandler())

symbol_table = SymbolTable()
global_scope = symbol_table.new_scope(kind="global", name="global")
walker = Walker(dispatch)

ctx = Context(scopes=[global_scope])

walker.walk(root, ctx, symbol_table)


def format_stack(ctx):
    lines = []
    for i, n in enumerate(ctx.stack):
        lines.append(
            f"  [{i}] {str(n)} :: '{n.snippet()}'"
        )
    return "\n".join(lines)

for vnode, ctx in walker._results:
    print("=" * 80)
    print(f"{type(vnode).__name__:10} "
        f"{str(vnode):30} ")
    print("STACK:")
    print(format_stack(ctx))

