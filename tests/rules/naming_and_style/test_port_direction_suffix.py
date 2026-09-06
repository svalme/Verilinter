import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.naming_and_style.port_direction_suffix import PortDirectionSuffixRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "PORT_DIRECTION_SUFFIX"]


class TestPortDirectionSuffixRule:
    @pytest.fixture
    def rule(self) -> PortDirectionSuffixRule:
        return PortDirectionSuffixRule()

    def test_rule_has_correct_code(self, rule: PortDirectionSuffixRule) -> None:
        assert rule.code == "PORT_DIRECTION_SUFFIX"

    def test_flags_input_port_missing_suffix(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a);
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_flags_output_port_missing_suffix(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(output logic y);
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_correctly_suffixed_ports(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input logic a_i, output logic y_o, inout wire b_io);
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_ordinary_internal_wire(self) -> None:
        diagnostics = _diagnostics(
            """
            module top;
              wire a;
            endmodule
            """
        )

        assert diagnostics == []
