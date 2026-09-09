import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.connectivity_and_hierarchy.instance_output_driver_conflict import InstanceOutputDriverConflictRule


ASSIGN_PLUS_INSTANCE_OUTPUT_CODE = """
module top;
  wire x, a;
  assign x = a;
  sub u_sub(.out(x));
endmodule

module sub(output wire out);
endmodule
"""

PROCEDURAL_WRITE_PLUS_INSTANCE_OUTPUT_CODE = """
module top(input logic clk);
  logic x;
  always_ff @(posedge clk) begin
    x <= 1'b1;
  end
  sub u_sub(.out(x));
endmodule

module sub(output logic out);
endmodule
"""

PLAIN_INSTANCE_OUTPUT_ONLY_CODE = """
module top;
  wire x;
  sub u_sub(.out(x));
endmodule

module sub(output wire out);
endmodule
"""

INPUT_PORT_WITH_OTHER_DRIVER_CODE = """
module top;
  wire a;
  assign a = 1'b1;
  sub u_sub(.in(a));
endmodule

module sub(input wire in);
endmodule
"""

UNDEFINED_MODULE_CODE = """
module top;
  wire x, a;
  assign x = a;
  sub u_sub(.out(x));
endmodule
"""


from tests.support.parse_diagnostics import assert_no_parse_errors


def _run(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_instance_output_driver_conflict.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return InstanceOutputDriverConflictRule().run(symbol_table)


class TestInstanceOutputDriverConflictRule:
    @pytest.fixture
    def rule(self) -> InstanceOutputDriverConflictRule:
        return InstanceOutputDriverConflictRule()

    def test_rule_has_correct_code(self, rule: InstanceOutputDriverConflictRule) -> None:
        assert rule.code == "INSTANCE_OUTPUT_DRIVER_CONFLICT"

    def test_flags_assign_plus_instance_output_conflict(self) -> None:
        diagnostics = _run(ASSIGN_PLUS_INSTANCE_OUTPUT_CODE)

        assert len(diagnostics) == 1
        assert "u_sub" in diagnostics[0]["message"]
        assert "x" in diagnostics[0]["message"]

    def test_flags_procedural_write_plus_instance_output_conflict(self) -> None:
        diagnostics = _run(PROCEDURAL_WRITE_PLUS_INSTANCE_OUTPUT_CODE)

        assert len(diagnostics) == 1

    def test_does_not_flag_instance_output_with_no_other_driver(self) -> None:
        assert _run(PLAIN_INSTANCE_OUTPUT_ONLY_CODE) == []

    def test_does_not_flag_input_bound_connection(self) -> None:
        assert _run(INPUT_PORT_WITH_OTHER_DRIVER_CODE) == []

    def test_does_not_flag_when_module_type_is_undefined(self) -> None:
        """UNDEFINED_MODULE's concern, not this rule's -- there's no real port
        list to resolve `out`'s direction against."""
        assert _run(UNDEFINED_MODULE_CODE) == []
