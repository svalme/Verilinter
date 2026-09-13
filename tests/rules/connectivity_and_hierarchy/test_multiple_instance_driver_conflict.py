import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.connectivity_and_hierarchy.multiple_instance_driver_conflict import MultipleInstanceDriverConflictRule


TWO_INSTANCES_DRIVE_SAME_NET_CODE = """
module top;
  wire x;
  sub u1(.out(x));
  sub u2(.out(x));
endmodule

module sub(output wire out);
endmodule
"""

THREE_INSTANCES_DRIVE_SAME_NET_CODE = """
module top;
  wire x;
  sub u1(.out(x));
  sub u2(.out(x));
  sub u3(.out(x));
endmodule

module sub(output wire out);
endmodule
"""

SINGLE_INSTANCE_ONLY_CODE = """
module top;
  wire x;
  sub u1(.out(x));
endmodule

module sub(output wire out);
endmodule
"""

DIFFERENT_NETS_CODE = """
module top;
  wire x, y;
  sub u1(.out(x));
  sub u2(.out(y));
endmodule

module sub(output wire out);
endmodule
"""

SAME_INSTANCE_TWO_OUTPUT_PORTS_CODE = """
module top;
  wire x;
  sub u1(.out1(x), .out2(x));
endmodule

module sub(output wire out1, output wire out2);
endmodule
"""

INPUT_PORTS_ONLY_CODE = """
module top;
  wire x;
  assign x = 1'b0;
  sub u1(.in(x));
  sub u2(.in(x));
endmodule

module sub(input wire in);
endmodule
"""

UNDEFINED_MODULE_CODE = """
module top;
  wire x;
  sub u1(.out(x));
  sub u2(.out(x));
endmodule
"""

GENERATE_IF_ELSE_MUTUALLY_EXCLUSIVE_INSTANCES_CODE = """
module top #(parameter FAST = 1, parameter EN = 0);
  wire x;
  generate if (FAST) begin
    fast_sub u1(.out(x));
  end else if (EN) begin
    slow_sub u1(.out(x));
  end endgenerate
endmodule

module fast_sub(output wire out);
endmodule

module slow_sub(output wire out);
endmodule
"""


from tests.support.parse_diagnostics import assert_no_parse_errors


def _run(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_multiple_instance_driver_conflict.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return MultipleInstanceDriverConflictRule().run(symbol_table)


class TestMultipleInstanceDriverConflictRule:
    @pytest.fixture
    def rule(self) -> MultipleInstanceDriverConflictRule:
        return MultipleInstanceDriverConflictRule()

    def test_rule_has_correct_code(self, rule: MultipleInstanceDriverConflictRule) -> None:
        assert rule.code == "MULTIPLE_INSTANCE_DRIVER_CONFLICT"

    def test_flags_two_instances_driving_same_net(self) -> None:
        diagnostics = _run(TWO_INSTANCES_DRIVE_SAME_NET_CODE)

        assert len(diagnostics) == 1
        assert "u2" in diagnostics[0]["message"]
        assert "u1" in diagnostics[0]["message"]
        assert "x" in diagnostics[0]["message"]

    def test_flags_each_additional_instance_against_the_first_driver(self) -> None:
        diagnostics = _run(THREE_INSTANCES_DRIVE_SAME_NET_CODE)

        assert len(diagnostics) == 2
        assert all("u1" in d["message"] for d in diagnostics)

    def test_does_not_flag_single_driving_instance(self) -> None:
        assert _run(SINGLE_INSTANCE_ONLY_CODE) == []

    def test_does_not_flag_instances_driving_different_nets(self) -> None:
        assert _run(DIFFERENT_NETS_CODE) == []

    def test_does_not_flag_one_instance_driving_two_of_its_own_ports(self) -> None:
        """Deliberately out of scope: this rule targets conflicts between distinct
        instances, not one instance binding two of its own output ports to the
        same net."""
        assert _run(SAME_INSTANCE_TWO_OUTPUT_PORTS_CODE) == []

    def test_does_not_flag_input_bound_connections(self) -> None:
        assert _run(INPUT_PORTS_ONLY_CODE) == []

    def test_does_not_flag_when_module_type_is_undefined(self) -> None:
        """UNDEFINED_MODULE's concern, not this rule's -- there's no real port
        list to resolve `out`'s direction against."""
        assert _run(UNDEFINED_MODULE_CODE) == []

    def test_does_not_flag_generate_if_else_mutually_exclusive_instances(self) -> None:
        """The same instance name reused across `generate if`/`else if` branches to
        select one of several implementations is never simultaneously instantiated, so it is not a
        real two-instances-drive-one-net conflict."""
        assert _run(GENERATE_IF_ELSE_MUTUALLY_EXCLUSIVE_INSTANCES_CODE) == []
