from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.fsms.missing_default_on_state_case import MissingDefaultOnStateCaseRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = parse_text(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "MISSING_DEFAULT_ON_STATE_CASE"]


class TestMissingDefaultOnStateCaseRule:
    @pytest.fixture
    def rule(self) -> MissingDefaultOnStateCaseRule:
        return MissingDefaultOnStateCaseRule()

    def test_rule_has_correct_code(self, rule: MissingDefaultOnStateCaseRule) -> None:
        assert rule.code == "MISSING_DEFAULT_ON_STATE_CASE"

    def test_flags_state_case_missing_default(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, output reg y);
              localparam IDLE = 2'b00;
              localparam RUN  = 2'b01;
              reg [1:0] state;
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) state <= IDLE;
                else case (state)
                  IDLE: state <= RUN;
                  RUN: state <= IDLE;
                endcase
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_state_case_with_default(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, output reg y);
              localparam IDLE = 2'b00;
              localparam RUN  = 2'b01;
              reg [1:0] state;
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) state <= IDLE;
                else case (state)
                  IDLE: state <= RUN;
                  RUN: state <= IDLE;
                  default: state <= IDLE;
                endcase
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_ordinary_mux_missing_default(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [1:0] sel, output reg y);
              always @(*) begin
                case (sel)
                  2'b00: y = 1'b0;
                  2'b01: y = 1'b1;
                endcase
              end
            endmodule
            """
        )

        assert diagnostics == []
