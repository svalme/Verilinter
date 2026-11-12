from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol import Symbol
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.combinational_logic.no_multiple_drivers import NoMultipleDriversRule
from tests.support.parse_diagnostics import assert_no_parse_errors


MULTIPLE_DRIVERS_CODE = """
module top(input logic clk, input logic rst_n);
  logic x;
  always_ff @(posedge clk) begin
    x <= 1'b1;
  end
  always_ff @(negedge rst_n) begin
    x <= 1'b0;
  end
endmodule
"""

SINGLE_DRIVER_CODE = """
module top(input logic clk);
  logic x;
  always_ff @(posedge clk) begin
    x <= 1'b1;
    x <= 1'b0;
  end
endmodule
"""

DECLARATION_AND_SINGLE_BLOCK_CODE = """
module top(input logic clk);
  int x = 0;
  always_ff @(posedge clk) begin
    x <= 1;
  end
endmodule
"""

MULTIPLE_CONTINUOUS_ASSIGN_DRIVERS_CODE = """
module top(input logic a, input logic b);
  logic x;
  assign x = a;
  assign x = b;
endmodule
"""

MIXED_ASSIGN_AND_PROCEDURAL_DRIVERS_CODE = """
module top(input logic clk, input logic a);
  logic x;
  assign x = a;
  always_ff @(posedge clk) begin
    x <= 1'b0;
  end
endmodule
"""

SINGLE_CONTINUOUS_ASSIGN_DRIVER_CODE = """
module top(input logic a);
  logic x;
  assign x = a;
endmodule
"""


class TestNoMultipleDriversRule:
    @pytest.fixture
    def rule(self) -> NoMultipleDriversRule:
        return NoMultipleDriversRule()

    def test_rule_has_correct_code(self, rule: NoMultipleDriversRule) -> None:
        assert rule.code == "NO_MULTIPLE_DRIVERS"

    def test_flags_symbol_written_from_two_driver_sources(self, rule: NoMultipleDriversRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        sym.add_use(
            {"line": 4, "col": 5},
            write=True,
            driver_id="always:a.sv:3:3",
            driver_location={"line": 3, "col": 3, "file": "a.sv"},
        )
        sym.add_use(
            {"line": 7, "col": 5},
            write=True,
            driver_id="always:a.sv:6:3",
            driver_location={"line": 6, "col": 3, "file": "a.sv"},
        )
        st.global_scope.define(sym)

        diagnostics = rule.run(st)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_MULTIPLE_DRIVERS"
        assert diagnostics[0]["line"] == 7
        assert "x" in diagnostics[0]["message"]
        assert "line 3" in diagnostics[0]["message"]

    def test_does_not_flag_same_driver_block_writing_multiple_times(self, rule: NoMultipleDriversRule) -> None:
        st = SymbolTable()
        sym = Symbol(name="x", kind="variable")
        sym.add_declaration({"line": 2, "col": 9})
        sym.add_use(
            {"line": 4, "col": 5},
            write=True,
            driver_id="always:a.sv:3:3",
            driver_location={"line": 3, "col": 3, "file": "a.sv"},
        )
        sym.add_use(
            {"line": 5, "col": 5},
            write=True,
            driver_id="always:a.sv:3:3",
            driver_location={"line": 3, "col": 3, "file": "a.sv"},
        )
        st.global_scope.define(sym)

        assert rule.run(st) == []

    def test_does_not_flag_initializer_plus_one_procedural_driver(self, rule: NoMultipleDriversRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(DECLARATION_AND_SINGLE_BLOCK_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_no_multiple_drivers.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_against_real_parsed_source(self, rule: NoMultipleDriversRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(MULTIPLE_DRIVERS_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_no_multiple_drivers.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_MULTIPLE_DRIVERS"
        assert "x" in diagnostics[0]["message"]

    def test_single_driver_source_does_not_flag(self, rule: NoMultipleDriversRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(SINGLE_DRIVER_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_no_multiple_drivers.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_flags_two_continuous_assign_drivers(self, rule: NoMultipleDriversRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(MULTIPLE_CONTINUOUS_ASSIGN_DRIVERS_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_no_multiple_drivers.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_MULTIPLE_DRIVERS"
        assert "x" in diagnostics[0]["message"]

    def test_flags_continuous_assign_plus_procedural_driver(self, rule: NoMultipleDriversRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(MIXED_ASSIGN_AND_PROCEDURAL_DRIVERS_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_no_multiple_drivers.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_MULTIPLE_DRIVERS"
        assert "x" in diagnostics[0]["message"]

    def test_single_continuous_assign_driver_does_not_flag(self, rule: NoMultipleDriversRule) -> None:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(SINGLE_CONTINUOUS_ASSIGN_DRIVER_CODE)
        assert_no_parse_errors("tests/rules/combinational_logic/test_no_multiple_drivers.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_generate_if_else_mutually_exclusive_drivers_not_flagged(self, rule: NoMultipleDriversRule) -> None:
        """A signal driven from two `always` blocks in mutually exclusive
        `generate if`/`else` branches (a parameterized module/style choice) is
        not a real multi-driver conflict, since only one branch is ever
        elaborated."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(
            """
            module top #(parameter TWO_CYCLE = 1) (input logic clk, input logic a, input logic b);
              logic x;
              generate if (TWO_CYCLE) begin
                always @(posedge clk) begin
                  x <= a;
                end
              end else begin
                always @* begin
                  x = b;
                end
              end endgenerate
            endmodule
            """
        )
        assert_no_parse_errors("tests/rules/combinational_logic/test_no_multiple_drivers.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_generate_if_else_if_else_three_way_mutually_exclusive_not_flagged(
        self, rule: NoMultipleDriversRule
    ) -> None:
        """A three-way module selection (option A, option B, or neither): an
        `else if` chain, not just a plain `if`/`else`."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(
            """
            module top #(parameter FAST = 0, parameter EN = 0) (input logic a, input logic b);
              logic x;
              generate if (FAST) begin
                assign x = a;
              end else if (EN) begin
                assign x = b;
              end else begin
                assign x = 1'b0;
              end endgenerate
            endmodule
            """
        )
        assert_no_parse_errors("tests/rules/combinational_logic/test_no_multiple_drivers.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []

    def test_generate_if_does_not_suppress_a_real_conflict(self, rule: NoMultipleDriversRule) -> None:
        """Branch-exclusivity must not become a blanket exemption for anything
        touched by a generate block: a driver inside a generate-if branch and an
        unconditional driver outside it can both apply at once and must still
        flag."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(
            """
            module top #(parameter EN = 1) (input logic a, input logic b);
              logic x;
              generate if (EN) begin
                assign x = a;
              end endgenerate
              assign x = b;
            endmodule
            """
        )
        assert_no_parse_errors("tests/rules/combinational_logic/test_no_multiple_drivers.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        diagnostics = rule.run(symbol_table)

        assert len(diagnostics) == 1
        assert diagnostics[0]["code"] == "NO_MULTIPLE_DRIVERS"

    def test_reads_carrying_a_driver_id_are_not_treated_as_drivers(self, rule: NoMultipleDriversRule) -> None:
        """`IdentifierNameHandler` now computes `driver_id` for read events too
        (needed by COMBINATIONAL_LOOP), not just writes. This rule must keep
        ignoring read events entirely -- a signal read (never written) inside a
        combinational block must not be flagged as multiply-driven just because
        its read events now carry a `driver_id`."""
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)

        tree = parse_text(
            """
            module top;
              wire a, b, c;
              assign b = a;
              assign c = a;
            endmodule
            """
        )
        assert_no_parse_errors("tests/rules/combinational_logic/test_no_multiple_drivers.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)

        assert rule.run(symbol_table) == []


def _diagnostics(body: str, declarations: str = "logic [7:0] v; logic [3:0] i;") -> list[dict]:
    symbol_table = SymbolTable()
    walker = Walker(dispatch)
    tree = parse_text(f"module top(input logic clk, input logic a, input logic b); {declarations} {body} endmodule")
    assert_no_parse_errors("tests/rules/combinational_logic/test_no_multiple_drivers.py", tree)
    walker.walk(tree.root, tree, Context(scope=symbol_table.global_scope), symbol_table)
    return NoMultipleDriversRule().run(symbol_table)


class TestWritesToDifferentPartsOfOneVariable:
    @pytest.mark.parametrize(
        "body",
        [
            "assign v[0] = a; assign v[1] = b;",
            "assign v[3:0] = 4'h0; assign v[7:4] = 4'h0;",
            "assign v[7:4] = 4'h0; assign v[0] = a;",
            "localparam P = 4; assign v[P-1:0] = 4'h0; assign v[7:P] = 4'h0;",
            "assign v[0 +: 4] = 4'h0; assign v[4 +: 4] = 4'h0;",
            "always_comb v[0] = a; assign v[1] = b;",
        ],
    )
    def test_provably_disjoint_writes_are_not_multiple_drivers(self, body: str) -> None:
        assert _diagnostics(body) == []

    @pytest.mark.parametrize(
        "body",
        [
            "assign v[0] = a; assign v[0] = b;",
            "assign v[3:0] = 4'h0; assign v[4:1] = 4'h0;",
            "assign v = 8'h0; assign v[1] = b;",
            "assign v[i] = a; assign v[0] = b;",
            "assign v[i +: 2] = 2'h0; assign v[4 +: 4] = 4'h0;",
            "always_comb v[0] = a; always_comb v[0] = b;",
        ],
    )
    def test_overlapping_or_unknown_writes_still_conflict(self, body: str) -> None:
        assert len(_diagnostics(body)) == 1

    def test_array_elements_with_constant_indices(self) -> None:
        declarations = "logic [7:0] m [4];"
        assert _diagnostics("assign m[0] = 8'h0; assign m[1] = 8'h0;", declarations) == []
        assert len(_diagnostics("assign m[2] = 8'h0; assign m[2] = 8'h1;", declarations)) == 1

    def test_second_dimension_decides_when_the_first_is_the_same(self) -> None:
        declarations = "logic [3:0][7:0] w;"
        assert _diagnostics("assign w[1][0] = a; assign w[1][1] = b;", declarations) == []
        assert len(_diagnostics("assign w[1][0] = a; assign w[1][0] = b;", declarations)) == 1


class TestGenerateLoopWrites:
    _ARRAY = "logic [7:0] m [8];"
    _BITS = "logic [7:0] g;"

    @pytest.mark.parametrize(
        "decls, body",
        [
            (_ARRAY, "assign m[0] = 8'h0; for (genvar k = 1; k < 8; k++) begin : g assign m[k] = 8'h1; end"),
            (_ARRAY, "for (genvar k = 0; k < 7; k++) begin : g assign m[k] = 8'h1; end assign m[7] = 8'h0;"),
            (_BITS, "for (genvar k = 0; k < 4; k++) begin : g assign g[k*2] = a; assign g[k*2+1] = b; end"),
            (
                _BITS,
                "for (genvar k = 0; k < 4; k++) begin : g assign g[k] = a; end"
                " for (genvar j = 0; j < 4; j++) begin : h assign g[4+j] = b; end",
            ),
            (_BITS, "for (genvar k = 0; k < 8; k += 2) begin : g assign g[k] = a; end assign g[1] = b;"),
            (_BITS, "for (genvar k = 7; k >= 4; k--) begin : g assign g[k] = a; end assign g[0] = b;"),
        ],
    )
    def test_loop_writes_with_disjoint_index_sets_are_not_multiple_drivers(self, decls: str, body: str) -> None:
        assert _diagnostics(body, decls) == []

    @pytest.mark.parametrize(
        "decls, body",
        [
            (_ARRAY, "assign m[0] = 8'h0; for (genvar k = 0; k < 8; k++) begin : g assign m[k] = 8'h1; end"),
            (_BITS, "for (genvar k = 0; k < 4; k++) begin : g assign g[k] = a; end assign g[3] = b;"),
            (_BITS, "for (genvar k = 0; k < N; k++) begin : g assign g[k] = a; end assign g[0] = b;"),
            (_BITS, "for (genvar k = 0; k < 4; k++) begin : g assign g[k] = a; assign g[k] = b; end"),
        ],
    )
    def test_loop_writes_with_shared_or_unknown_indices_still_conflict(self, decls: str, body: str) -> None:
        assert len(_diagnostics(body, decls)) == 1

    def test_mutually_exclusive_conditions_inside_a_loop_are_not_multiple_drivers(self) -> None:
        body = """
        localparam W = 8;
        for (genvar k = 0; k < W; k++) begin : g
          if (k * 2 < W - 1) begin : reduce assign v[k] = a; end
          if (k * 2 == W - 1) begin : base assign v[k] = b; end
        end
        """
        assert _diagnostics(body) == []

    def test_casted_genvar_in_a_condition_is_evaluated(self) -> None:
        body = """
        localparam W = 8;
        for (genvar k = 0; k < W; k++) begin : g
          if (unsigned'(k) * 2 < W - 1) begin : reduce assign v[k] = a; end
          if (unsigned'(k) * 2 == W - 1) begin : base assign v[k] = b; end
        end
        """
        assert _diagnostics(body) == []

    def test_write_in_a_branch_the_defaults_switch_off_is_not_a_driver(self) -> None:
        body = "localparam EN = 0; if (EN) begin : g assign v[0] = a; end assign v[0] = b;"
        assert _diagnostics(body) == []

    def test_write_in_a_branch_the_defaults_switch_on_is_a_driver(self) -> None:
        body = "localparam EN = 1; if (EN) begin : g assign v[0] = a; end assign v[0] = b;"
        assert len(_diagnostics(body)) == 1


class TestStructMemberWrites:
    _DECLS = "typedef struct packed { logic [3:0] lo; logic [3:0] hi; } pair_t; pair_t s;"

    def test_distinct_members_are_not_multiple_drivers(self) -> None:
        assert _diagnostics("assign s.lo = 4'h0; assign s.hi = 4'h1;", self._DECLS) == []

    def test_same_member_from_two_drivers_conflicts(self) -> None:
        assert len(_diagnostics("assign s.lo = 4'h0; assign s.lo = 4'h1;", self._DECLS)) == 1

    def test_whole_struct_against_a_member_conflicts(self) -> None:
        assert len(_diagnostics("assign s = 8'h0; assign s.hi = 4'h1;", self._DECLS)) == 1
