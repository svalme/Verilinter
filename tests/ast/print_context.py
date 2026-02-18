
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import pyslang as sl

from src.pkg.ast.symbol_table import SymbolTable
from src.pkg.ast.context import Context
from src.pkg.ast.walker import Walker

from src.pkg.vnodes.syntax_vnode import SyntaxVNode
from src.pkg.vnodes.token_vnode import TokenVNode

from src.pkg.handlers.register_handlers import *
from src.pkg.ast.dispatch import dispatch

CODE = """
module top(input logic clk);
  real x;
  always @(posedge clk) begin
    a = b;
    c <= d;
  end
endmodule
"""

def print_context():
    tree = sl.SyntaxTree.fromText(CODE)
    root = SyntaxVNode(tree.root, tree)

    symbol_table = SymbolTable()
    global_scope = symbol_table.new_scope(kind="global", name="global")
    ctx = Context(scopes=[global_scope])
    walker = Walker(dispatch)
    walker.walk(root, tree, ctx, symbol_table)

    for vnode, ctx in walker._results:
        raw = vnode.raw

        kind = (
            raw.kind.name
            if isinstance(raw, sl.SyntaxNode)
            else raw.kind.name
        )

        node_type = vnode.__class__.__name__
        loc = vnode.location
        loc_str = f"{loc['line']}:{loc['col']}" if loc else "?:?"

        print(f"{node_type:<12} {kind:<30} @ {loc_str}")
        print(f"  Context: {ctx}")
        print()

print_context()