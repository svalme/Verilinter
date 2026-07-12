import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.symbol.read_before_write_rule import ReadBeforeWriteRule


READ_BEFORE_WRITE_CODE = """
module top;
  real x;
  real y;
  initial begin
    y = x;
    x = 1;
  end
endmodule
"""


WRITE_BEFORE_READ_CODE = """
module top;
  real x;
  initial begin
    x = 1;
    x = x;
  end
endmodule
"""

COMPLEX_LVALUE_CODE = """
module top;
  logic [7:0] a, b;
  logic [7:0] arr [0:3];
  typedef struct packed { logic [7:0] x; } foo_t;
  foo_t s;
  initial begin
    a[0] = b[0];
    arr[1] = a;
    s.x = b;
    {a[1], b[1]} = 2'b01;
  end
endmodule
"""


class TestReadBeforeWriteRule:
    @pytest.fixture
    def rule(self) -> ReadBeforeWriteRule:
        return ReadBeforeWriteRule()

    def test_rule_has_correct_code(self, rule: ReadBeforeWriteRule) -> None:
        assert rule.code == "READ_BEFORE_WRITE"

    def test_flags_symbol_read_before_any_write(self, rule: ReadBeforeWriteRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 8})
        sym.add_use({"line": 4, "col": 5}, read=True)
        sym.add_use({"line": 5, "col": 5}, write=True)
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "READ_BEFORE_WRITE"
        assert diagnostics[0]["line"] == 4
        assert diagnostics[0]["col"] == 5
        assert "x" in diagnostics[0]["message"]

    def test_does_not_flag_symbol_written_before_read(self, rule: ReadBeforeWriteRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 8})
        sym.add_use({"line": 4, "col": 5}, write=True)
        sym.add_use({"line": 5, "col": 5}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_against_real_parsed_source(self, rule: ReadBeforeWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(READ_BEFORE_WRITE_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "READ_BEFORE_WRITE"
        assert "x" in diagnostics[0]["message"]

    def test_does_not_flag_when_source_writes_before_read(self, rule: ReadBeforeWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(WRITE_BEFORE_READ_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_complex_lvalues_count_as_writes(self, rule: ReadBeforeWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(COMPLEX_LVALUE_CODE)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)
        flagged_names = {d["message"].split("'")[1] for d in diagnostics}

        assert "arr" not in flagged_names
        assert "s" not in flagged_names
