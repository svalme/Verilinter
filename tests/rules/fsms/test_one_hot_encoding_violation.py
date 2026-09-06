import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.fsms.one_hot_encoding_violation import OneHotEncodingViolationRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "ONE_HOT_ENCODING_VIOLATION"]


class TestOneHotEncodingViolationRule:
    @pytest.fixture
    def rule(self) -> OneHotEncodingViolationRule:
        return OneHotEncodingViolationRule()

    def test_rule_has_correct_code(self, rule: OneHotEncodingViolationRule) -> None:
        assert rule.code == "ONE_HOT_ENCODING_VIOLATION"

    def test_flags_non_one_hot_value_in_one_hot_width_register(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, output reg y);
              localparam IDLE = 3'b001;
              localparam RUN  = 3'b010;
              localparam DONE = 3'b011;
              reg [2:0] state;
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) state <= IDLE;
                else case (state)
                  IDLE: state <= RUN;
                  RUN: state <= DONE;
                  DONE: state <= IDLE;
                  default: state <= IDLE;
                endcase
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_proper_one_hot_encoding(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, output reg y);
              localparam IDLE = 3'b001;
              localparam RUN  = 3'b010;
              localparam DONE = 3'b100;
              reg [2:0] state;
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) state <= IDLE;
                else case (state)
                  IDLE: state <= RUN;
                  RUN: state <= DONE;
                  DONE: state <= IDLE;
                  default: state <= IDLE;
                endcase
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_ordinary_binary_encoding(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, output reg y);
              localparam IDLE = 2'b00;
              localparam RUN  = 2'b01;
              localparam DONE = 2'b10;
              localparam ERR  = 2'b11;
              reg [1:0] state;
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) state <= IDLE;
                else case (state)
                  IDLE: state <= RUN;
                  RUN: state <= DONE;
                  DONE: state <= ERR;
                  default: state <= IDLE;
                endcase
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_two_state_toggle_with_oversized_register(self) -> None:
        # A 2-state FSM is commonly declared with a 2-bit register anyway
        # (headroom for future states); width == state_count would otherwise
        # coincidentally look like one-hot intent here even though this is
        # completely ordinary binary-style code (IDLE=0 has popcount 0).
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

    def test_does_not_flag_ordinary_non_fsm_case(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input [2:0] sel, output reg y);
              always @(*) begin
                case (sel)
                  3'b001: y = 1'b0;
                  3'b010: y = 1'b1;
                  3'b011: y = 1'b0;
                  default: y = 1'b0;
                endcase
              end
            endmodule
            """
        )

        assert diagnostics == []
