from pathlib import Path
import pyslang as sl

# force handler registration
from src.pkg.handlers.register_handlers import *
from src.pkg.walk.dispatch import dispatch

from src.pkg.walk.walker import Walker
from src.pkg.walk.context import Context
from src.pkg.semantic.symbol_table import SymbolTable

DATA = Path(__file__).resolve().parents[3] / "data"


def test_identifier_debug():

    tree = sl.SyntaxTree.fromFile(str(DATA / "simple.v"))

    symbol_table = SymbolTable()
    walker = Walker(dispatch)

    ctx = Context(scope=symbol_table.global_scope)

    print("\n=== Starting AST walk ===")

    walker.walk(tree.root, tree, ctx, symbol_table)

    print("\n=== Final symbol table ===")
    print(symbol_table)
