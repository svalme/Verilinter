from pathlib import Path
import pyslang as sl

# force handler registration
from src.pkg.handlers.register_handlers import *

from src.pkg.ast.walker import Walker
from src.pkg.ast.context import Context
from src.pkg.ast.symbol_table import SymbolTable
from src.pkg.vnodes.syntax_vnode import SyntaxVNode
from tests.ast.test_symbol_table import symbol_table

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"


def test_identifier_debug():

    tree = sl.SyntaxTree.fromFile(str(DATA / "simple.v"))

    symbol_table = SymbolTable()
    global_scope = symbol_table.new_scope(kind="global", name="global")
    walker = Walker(dispatch)

    ctx = Context(scopes=[global_scope])

    print("\n=== Starting AST walk ===")

    walker.walk(tree.root, tree, ctx, symbol_table)

    print("\n=== Final symbol table ===")
    print(symbol_table)
