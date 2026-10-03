from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.connectivity_and_hierarchy.undriven_tristate_signal import UndrivenTristateSignalRule


from tests.support.parse_diagnostics import assert_no_parse_errors


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    assert_no_parse_errors("tests/rules/connectivity_and_hierarchy/test_undriven_tristate_signal.py", tree)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return UndrivenTristateSignalRule().run(symbol_table)


class TestUndrivenTristateSignalRule:
    @pytest.fixture
    def rule(self) -> UndrivenTristateSignalRule:
        return UndrivenTristateSignalRule()

    def test_rule_has_correct_code(self, rule: UndrivenTristateSignalRule) -> None:
        assert rule.code == "UNDRIVEN_TRISTATE_SIGNAL"

    def test_flags_internal_net_with_single_tristate_driver(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input en, input [3:0] d, output [3:0] q);
              wire [3:0] bus;
              assign bus = en ? d : 4'bzzzz;
              assign q = bus;
            endmodule
            """
        )

        assert len(diagnostics) == 1
        assert "bus" in diagnostics[0]["message"]

    def test_flags_reversed_ternary_branch_order(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input en, input [3:0] d, output [3:0] q);
              wire [3:0] bus;
              assign bus = en ? 4'bzzzz : d;
              assign q = bus;
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_port_net(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input en, input [3:0] d, inout [3:0] bus);
              assign bus = en ? d : 4'bzzzz;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_net_connected_to_instance(self) -> None:
        diagnostics = _diagnostics(
            """
            module sub(inout [3:0] p);
            endmodule
            module top(input en, input [3:0] d);
              wire [3:0] bus;
              assign bus = en ? d : 4'bzzzz;
              sub u1(.p(bus));
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_net_with_two_drivers(self) -> None:
        # Two drivers on the same net -- NO_MULTIPLE_DRIVERS' territory,
        # regardless of either driver's tri-state intent.
        diagnostics = _diagnostics(
            """
            module top(input en1, input en2, input [3:0] d1, input [3:0] d2, output [3:0] q);
              wire [3:0] bus;
              assign bus = en1 ? d1 : 4'bzzzz;
              assign bus = en2 ? d2 : 4'bzzzz;
              assign q = bus;
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_non_tristate_single_driver(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [3:0] d, output [3:0] q);
              wire [3:0] bus;
              assign bus = d;
              assign q = bus;
            endmodule
            """
        )

        assert diagnostics == []
