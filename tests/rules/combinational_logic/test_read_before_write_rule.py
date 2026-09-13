import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.combinational_logic.read_before_write_rule import ReadBeforeWriteRule
from tests.support.parse_diagnostics import assert_no_parse_errors


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

COMPOUND_ASSIGN_BEFORE_WRITE_CODE = """
module top;
  int x;
  initial begin
    x += 1;
  end
endmodule
"""

INCREMENT_BEFORE_WRITE_CODE = """
module top;
  int x;
  initial begin
    ++x;
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

DECLARATION_INITIALIZER_BEFORE_READ_CODE = """
module top;
  int x = 1;
  int y;
  initial begin
    y = x;
  end
endmodule
"""

DECLARATION_WITHOUT_INITIALIZER_BEFORE_READ_CODE = """
module top;
  int x;
  int y;
  initial begin
    y = x;
  end
endmodule
"""

INPUT_PORT_READ_CODE = """
module top(input logic clk, input logic d, output logic q);
  always_ff @(posedge clk) begin
    q <= d;
  end
endmodule
"""

OUTPUT_PORT_READ_BEFORE_WRITE_CODE = """
module top(output logic y);
  logic z;
  always_comb begin
    z = y;
  end
endmodule
"""

CROSS_CONSTRUCT_READ_CODE = """
module top;
  logic a, b, c;
  assign c = a;
  assign a = b;
endmodule
"""

REGISTER_FEEDBACK_CODE = """
module top(input logic clk);
  logic [3:0] timer;
  always @(posedge clk) begin
    if (timer > 0)
      timer <= timer - 1;
  end
endmodule
"""

SAME_BLOCK_BLOCKING_ORDER_CODE = """
module top;
  logic a, b, c;
  always @* begin
    c = a;
    a = b;
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
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
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
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_flags_compound_assignment_before_any_prior_write(self, rule: ReadBeforeWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(COMPOUND_ASSIGN_BEFORE_WRITE_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "READ_BEFORE_WRITE"
        assert "x" in diagnostics[0]["message"]

    def test_flags_increment_before_any_prior_write(self, rule: ReadBeforeWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(INCREMENT_BEFORE_WRITE_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "READ_BEFORE_WRITE"
        assert "x" in diagnostics[0]["message"]

    def test_complex_lvalues_count_as_writes(self, rule: ReadBeforeWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(COMPLEX_LVALUE_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)
        flagged_names = {d["message"].split("'")[1] for d in diagnostics}

        assert "arr" not in flagged_names
        assert "s" not in flagged_names

    def test_declaration_initializer_counts_as_prior_write(self, rule: ReadBeforeWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(DECLARATION_INITIALIZER_BEFORE_READ_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_declaration_without_initializer_still_flags_read_before_write(self, rule: ReadBeforeWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(DECLARATION_WITHOUT_INITIALIZER_BEFORE_READ_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "READ_BEFORE_WRITE"
        assert "x" in diagnostics[0]["message"]

    def test_does_not_flag_input_port_read_with_no_local_write(self, rule: ReadBeforeWriteRule) -> None:
        """A read of an `input` port with no local write is the normal case -- the value
        comes from outside this scope, not a read-before-write bug."""
        st = SymbolTable()
        sym = Symbol(name="d", kind="variable")
        sym.is_port = True
        sym.port_direction = "input"
        sym.add_declaration({"line": 1, "col": 8})
        sym.add_use({"line": 3, "col": 5}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_inout_port_read_with_no_local_write(self, rule: ReadBeforeWriteRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="io", kind="variable")
        sym.is_port = True
        sym.port_direction = "inout"
        sym.add_declaration({"line": 1, "col": 8})
        sym.add_use({"line": 3, "col": 5}, read=True)
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_still_flags_output_port_read_before_local_write(self, rule: ReadBeforeWriteRule) -> None:
        """Output ports keep the check: reading one before it's ever locally driven is
        the real undriven-output bug shape (companion to NO_UNDRIVEN_OUTPUT_PORT)."""
        st = SymbolTable()
        sym = Symbol(name="y", kind="variable")
        sym.is_port = True
        sym.port_direction = "output"
        sym.add_declaration({"line": 1, "col": 8})
        sym.add_use({"line": 3, "col": 5}, read=True)
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert "y" in diagnostics[0]["message"]

    def test_against_real_source_does_not_flag_input_ports(self, rule: ReadBeforeWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(INPUT_PORT_READ_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_source_still_flags_output_port(self, rule: ReadBeforeWriteRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(OUTPUT_PORT_READ_BEFORE_WRITE_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert any("y" in d["message"] for d in diagnostics)

    def test_does_not_flag_read_in_a_different_concurrent_construct(self, rule: ReadBeforeWriteRule) -> None:
        """`a` is read in one `assign` and written in a separate, later `assign`.
        Continuous assigns are concurrent, order-independent constructs -- which
        one appears first in the file proves nothing about execution order, so
        this is not a real hazard even though the read textually precedes the
        write."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(CROSS_CONSTRUCT_READ_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)
        assert not any("'a'" in d["message"] for d in diagnostics)

    def test_does_not_flag_register_reading_its_own_value_before_nonblocking_update(
        self, rule: ReadBeforeWriteRule
    ) -> None:
        """`timer` is read (in the `if` condition) before its own later
        non-blocking update in the same clocked block -- normal sequential
        feedback (the register already holds a value from the previous clock
        edge), not an uninitialized read."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(REGISTER_FEEDBACK_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_still_flags_same_block_blocking_assignment_order(self, rule: ReadBeforeWriteRule) -> None:
        """`a` is read (`c = a;`) before its own later blocking write (`a = b;`)
        in the very same `always @*` block -- a genuine same-pass evaluation-order
        hazard, the case this rule exists to catch."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = sl.SyntaxTree.fromText(SAME_BLOCK_BLOCKING_ORDER_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_read_before_write_rule.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)
        assert any("'a'" in d["message"] for d in diagnostics)
