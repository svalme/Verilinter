import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.symbol.combinational_loop import CombinationalLoopRule


ASSIGN_LOOP_CODE = """
module top;
  wire a, b;
  assign a = b;
  assign b = a;
endmodule
"""

ALWAYS_COMB_LOOP_CODE = """
module top;
  logic a, b;
  always_comb begin
    a = b;
  end
  always_comb begin
    b = a;
  end
endmodule
"""

SEQUENTIAL_FEEDBACK_CODE = """
module top(input logic clk);
  logic [3:0] q;
  always_ff @(posedge clk) begin
    q <= q + 1;
  end
endmodule
"""

ACYCLIC_CHAIN_CODE = """
module top;
  wire a, b, c;
  assign b = a;
  assign c = b;
endmodule
"""

SELF_ASSIGNMENT_CODE = """
module top;
  wire a;
  assign a = a;
endmodule
"""


def _run(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return CombinationalLoopRule().run(symbol_table)


class TestCombinationalLoopRule:
    @pytest.fixture
    def rule(self) -> CombinationalLoopRule:
        return CombinationalLoopRule()

    def test_rule_has_correct_code(self, rule: CombinationalLoopRule) -> None:
        assert rule.code == "COMBINATIONAL_LOOP"

    def test_flags_two_signal_assign_loop(self) -> None:
        diagnostics = _run(ASSIGN_LOOP_CODE)

        assert len(diagnostics) == 1
        assert "a" in diagnostics[0]["message"]
        assert "b" in diagnostics[0]["message"]

    def test_flags_two_signal_always_comb_loop(self) -> None:
        diagnostics = _run(ALWAYS_COMB_LOOP_CODE)

        assert len(diagnostics) == 1

    def test_does_not_flag_sequential_feedback(self) -> None:
        """`always_ff` register feedback (`q <= q + 1;`) is normal sequential
        logic, never a combinational loop."""
        assert _run(SEQUENTIAL_FEEDBACK_CODE) == []

    def test_does_not_flag_acyclic_combinational_chain(self) -> None:
        assert _run(ACYCLIC_CHAIN_CODE) == []

    def test_does_not_flag_self_assignment(self) -> None:
        """`a = a;` is NO_SELF_ASSIGNMENT's concern, not a one-node cycle here."""
        assert _run(SELF_ASSIGNMENT_CODE) == []
