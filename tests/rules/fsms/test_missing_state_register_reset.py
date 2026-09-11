import pyslang as sl
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.register_rules import rule_runner
from src.pkg.rules.fsms.missing_state_register_reset import MissingStateRegisterResetRule


def _diagnostics(code: str) -> list[dict]:
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)

    tree = sl.SyntaxTree.fromText(code)
    walker.walk(tree.root, tree, ctx, symbol_table)

    return [d for d in rule_runner.run(walker.results) if d["code"] == "MISSING_STATE_REGISTER_RESET"]


class TestMissingStateRegisterResetRule:
    @pytest.fixture
    def rule(self) -> MissingStateRegisterResetRule:
        return MissingStateRegisterResetRule()

    def test_rule_has_correct_code(self, rule: MissingStateRegisterResetRule) -> None:
        assert rule.code == "MISSING_STATE_REGISTER_RESET"

    def test_flags_reset_branch_that_does_not_touch_state(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, output reg y, output reg z);
              localparam IDLE = 2'b00;
              localparam RUN  = 2'b01;
              reg [1:0] state;
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) z <= 1'b0;
                else case (state)
                  IDLE: state <= RUN;
                  RUN: state <= IDLE;
                  default: state <= IDLE;
                endcase
              end
            endmodule
            """
        )

        assert len(diagnostics) == 1

    def test_does_not_flag_reset_branch_covering_state_active_low(self) -> None:
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

    def test_does_not_flag_reset_branch_covering_state_active_high(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst, output reg y);
              localparam IDLE = 2'b00;
              localparam RUN  = 2'b01;
              reg [1:0] state;
              always @(posedge clk or posedge rst) begin
                if (rst) state <= IDLE;
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

    def test_does_not_flag_sync_reset_block(self) -> None:
        # Sync-reset has no structural marker to check by -- deliberately not
        # attempted, same restraint as ASYNC_RESET_XZ_VALUE/RESET_SIGNAL_NAMING.
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst, output reg y);
              localparam IDLE = 2'b00;
              localparam RUN  = 2'b01;
              reg [1:0] state;
              always @(posedge clk) begin
                if (rst) state <= IDLE;
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

    def test_does_not_flag_missing_reset_under_inverted_reset_polarity(self) -> None:
        # Documents a known limitation, not a claim of coverage:
        # `is_state_register_reset_covered` assumes the conventional polarity
        # where reset is asserted in the `if`-branch. Here reset (`rst_n` low)
        # is asserted in the `else`-branch instead, and `state` is genuinely
        # never assigned there -- a real missing-reset bug -- but the rule
        # only inspects the `if`-branch, finds `state` assigned by the FSM's
        # own transition case there, and concludes (wrongly) that it is
        # covered.
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, output reg z);
              localparam IDLE = 2'b00;
              localparam RUN  = 2'b01;
              reg [1:0] state;
              always @(posedge clk or negedge rst_n) begin
                if (rst_n) case (state)
                  IDLE: state <= RUN;
                  RUN: state <= IDLE;
                  default: state <= IDLE;
                endcase
                else z <= 1'b0;
              end
            endmodule
            """
        )

        assert diagnostics == []

    def test_does_not_flag_ordinary_non_fsm_case(self) -> None:
        diagnostics = _diagnostics(
            """
            module top(input clk, input rst_n, input [1:0] sel, output reg y);
              always @(posedge clk or negedge rst_n) begin
                if (!rst_n) y <= 1'b0;
                else case (sel)
                  2'b00: y <= 1'b0;
                  2'b01: y <= 1'b1;
                  default: y <= 1'b0;
                endcase
              end
            endmodule
            """
        )

        assert diagnostics == []
