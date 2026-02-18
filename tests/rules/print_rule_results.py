import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

# handlers
from src.pkg.handlers.register_handlers import *

from src.pkg.rules.register_rules import *

import pyslang as sl

from src.pkg.vnodes.syntax_vnode import SyntaxVNode
from src.pkg.ast.symbol_table import SymbolTable
from src.pkg.ast.context import Context
from src.pkg.ast.walker import Walker

from pathlib import Path
ROOT = Path(__file__).parent.parent
path = ROOT / "data" / "simple.v"
tree = sl.SyntaxTree.fromFile(str(path))


root = SyntaxVNode(tree.root, tree)

from src.pkg.ast.dispatch import dispatch

symbol_table = SymbolTable()
global_scope = symbol_table.new_scope(kind="global", name="global")
walker = Walker(dispatch)

ctx = Context(scopes=[global_scope])

walker.walk(root, tree, ctx, symbol_table)

diagnostics = rule_runner.run(walker._results)

for d in diagnostics:
    print(d)


#  running UnusedVariableRule
uv = UnusedVariableRule()

uv_diag = uv.run(symbol_table)
print("UnusedVariableRule diagnostics:")
for d in uv_diag:
    print(d)


#  running UndeclaredVariableRule
udv = UndeclaredVariableRule()

udv_diag = udv.run(symbol_table)
print("UndeclaredVariableRule diagnostics:")
for d in udv_diag:
    print(d)