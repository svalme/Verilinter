from src.pkg.parser.parse import parse_text
import pytest

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.combinational_logic.read_before_write_rule import ReadBeforeWriteRule
from tests.support.parse_diagnostics import assert_no_parse_errors


class TestReadBeforeWriteControlFlow:
    @pytest.fixture
    def rule(self) -> ReadBeforeWriteRule:
        return ReadBeforeWriteRule()

    def _run_rule(self, code: str, rule: ReadBeforeWriteRule) -> list[dict]:
        symbol_table = SymbolTable()
        ctx = Context(scope=symbol_table.global_scope)
        walker = Walker(dispatch)
        tree = parse_text(code)
        assert_no_parse_errors("test_read_before_write_control_flow.py", tree)
        walker.walk(tree.root, tree, ctx, symbol_table)
        return rule.run(symbol_table)

    def test_enum_member_in_always_comb_does_not_flag(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module top;
          typedef enum logic [1:0] { IDLE = 2'b00, BUSY = 2'b01 } state_e;
          state_e current_state;
          logic out;
          always_comb begin
            if (current_state == IDLE)
              out = 1'b0;
            else
              out = 1'b1;
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert not any("IDLE" in d["message"] for d in diagnostics)

    def test_shorthand_port_connection_does_not_flag(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module sub(input logic clk, output logic data_out);
        endmodule

        module top(input logic clk);
          logic data_out;
          logic data_copy;
          sub u_sub (.clk, .data_out);
          always_comb begin
            data_copy = data_out;
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert not any("data_out" in d["message"] for d in diagnostics)

    def test_type_query_bits_argument_does_not_flag(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module top;
          typedef struct packed { logic [7:0] a; logic [7:0] b; } packet_t;
          packet_t pkt;
          localparam int PKT_SZ = $bits(pkt);
          int w;
          always_comb begin
            w = $bits(pkt);
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert not any("pkt" in d["message"] for d in diagnostics)

    def test_complete_if_else_collapses_and_does_not_flag(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module top(input logic cond, input logic in_a, input logic in_b, output logic out_y);
          logic tmp;
          always_comb begin
            if (cond) begin
              tmp = in_a;
            end else begin
              tmp = in_b;
            end
            out_y = tmp;
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert not any("tmp" in d["message"] for d in diagnostics)

    def test_complete_if_else_if_else_chain_collapses_and_does_not_flag(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module top(input logic [1:0] sel, output logic [7:0] out_val);
          logic [7:0] temp;
          always_comb begin
            if (sel == 2'b00) begin
              temp = 8'h10;
            end else if (sel == 2'b01) begin
              temp = 8'h20;
            end else begin
              temp = 8'h00;
            end
            out_val = temp;
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert not any("temp" in d["message"] for d in diagnostics)

    def test_incomplete_if_without_else_flags_subsequent_read(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module top(input logic cond, input logic in_a, output logic out_y);
          logic tmp;
          always_comb begin
            if (cond) begin
              tmp = in_a;
            end
            out_y = tmp;
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert any("tmp" in d["message"] for d in diagnostics)

    def test_incomplete_else_if_without_final_else_flags_subsequent_read(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module top(input logic [1:0] sel, output logic [7:0] out_val);
          logic [7:0] temp;
          always_comb begin
            if (sel == 2'b00) begin
              temp = 8'h10;
            end else if (sel == 2'b01) begin
              temp = 8'h20;
            end
            out_val = temp;
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert any("temp" in d["message"] for d in diagnostics)

    def test_complete_case_with_default_collapses_and_does_not_flag(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module top(input logic [1:0] sel, output logic [7:0] out_val);
          logic [7:0] temp;
          always_comb begin
            case (sel)
              2'b00: temp = 8'h01;
              2'b01: temp = 8'h02;
              default: temp = 8'h00;
            endcase
            out_val = temp;
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert not any("temp" in d["message"] for d in diagnostics)

    def test_complete_unique_case_without_default_collapses_and_does_not_flag(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module top(input logic [1:0] sel, output logic [7:0] out_val);
          logic [7:0] temp;
          always_comb begin
            unique case (sel)
              2'b00: temp = 8'h01;
              2'b01: temp = 8'h02;
              2'b10: temp = 8'h03;
              2'b11: temp = 8'h04;
            endcase
            out_val = temp;
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert not any("temp" in d["message"] for d in diagnostics)

    def test_incomplete_case_without_default_flags_subsequent_read(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module top(input logic [1:0] sel, output logic [7:0] out_val);
          logic [7:0] temp;
          always_comb begin
            case (sel)
              2'b00: temp = 8'h01;
              2'b01: temp = 8'h02;
            endcase
            out_val = temp;
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert any("temp" in d["message"] for d in diagnostics)

    def test_case_with_empty_default_statement_flags_subsequent_read(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module top(input logic [1:0] sel, output logic [7:0] out_val);
          logic [7:0] temp;
          always_comb begin
            case (sel)
              2'b00: temp = 8'h01;
              default: ;
            endcase
            out_val = temp;
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert any("temp" in d["message"] for d in diagnostics)

    def test_predicate_read_before_write_flags_hazard(self, rule: ReadBeforeWriteRule) -> None:
        code = """
        module top(input logic in_v, output logic out_v);
          logic flag;
          always_comb begin
            if (flag) begin
              out_v = 1'b1;
            end else begin
              out_v = 1'b0;
            end
            flag = in_v;
          end
        endmodule
        """
        diagnostics = self._run_rule(code, rule)
        assert any("flag" in d["message"] for d in diagnostics)
