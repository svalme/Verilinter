"""Regression tests for task body contexts, driver assignments, and formal argument directions."""
import pytest
import pyslang as sl

from src.pkg.walk.context import Context
from src.pkg.walk.dispatch import dispatch
from src.pkg.semantic.symbol_table import SymbolTable
from src.pkg.walk.walker import Walker
from src.pkg.handlers.register_handlers import *
from src.pkg.rules.rule_runner import rule_runner
from src.pkg.rules.register_rules import *
from src.pkg.rules.sequential_logic.no_blocking_sequential_logic import NoBlockingAssignmentInSequentialRule
from src.pkg.rules.combinational_logic.no_nonblocking_comb import NoNonBlockingAssignmentInCombRule
from src.pkg.rules.combinational_logic.read_before_write_rule import ReadBeforeWriteRule


def _analyze_source(source: str):
    symbol_table = SymbolTable()
    ctx = Context(scope=symbol_table.global_scope)
    walker = Walker(dispatch)
    tree = sl.SyntaxTree.fromText(source)
    walker.walk(tree.root, tree, ctx, symbol_table)
    return tree, symbol_table


class TestTaskBodyDriverRegressions:
    """Test task body contexts, variable scoping, and assignment semantics."""

    def test_task_local_variable_assignment_does_not_leak_to_module(self):
        """Assignments to task-local variables must update only the task-level symbol."""
        source = """
        module m;
          reg [7:0] counter;
          task automatic compute(input [7:0] in_val);
            reg [7:0] local_temp;
            local_temp = in_val + 8'd1;
          endtask
        endmodule
        """
        tree, symbol_table = _analyze_source(source)
        module_scope = symbol_table.lookup_module("m")
        assert module_scope is not None
        assert "local_temp" not in module_scope.symbols

        task_scope = next(c for c in module_scope.children if c.kind == "task" and c.name == "compute")
        assert "local_temp" in task_scope.symbols
        local_temp_sym = task_scope.symbols["local_temp"]
        assert local_temp_sym.write_count == 1
        assert local_temp_sym.is_written

        # Module-level counter should be untouched
        counter_sym = module_scope.lookup("counter")
        assert counter_sym.write_count == 0

    def test_task_body_assignment_to_module_variable_resolves_and_records_write(self):
        """When a task body writes to a module-level variable, lexical lookup resolves
        the module symbol and records write/read events without an enclosing procedural driver."""
        source = """
        module m;
          reg [7:0] counter;
          task automatic step_counter();
            counter = counter + 8'd1;
          endtask
        endmodule
        """
        tree, symbol_table = _analyze_source(source)
        module_scope = symbol_table.lookup_module("m")
        assert module_scope is not None
        counter_sym = module_scope.lookup("counter")
        assert counter_sym is not None
        assert counter_sym.write_count == 1
        assert counter_sym.read_count == 1

        # The write occurred inside a task declaration, so driver_id is None
        write_events = [e for e in counter_sym.use_events if e["write"]]
        assert len(write_events) == 1
        assert write_events[0].get("driver_id") is None

    def test_blocking_in_sequential_rule_behavior_in_task_vs_procedural_blocks(self):
        """NO_BLOCKING_SEQUENTIAL applies to sequential procedural blocks (always @posedge clk).
        Inside a task declaration, assignments are outside procedural blocks, so NO_BLOCKING_SEQUENTIAL
        is not directly triggered on the task declaration."""
        from tests.support.lint_harness import run_inline_lint_case

        # 1. Direct sequential block with blocking assignment -> flagged
        res_seq = run_inline_lint_case({
            "top.sv": """
            module m(input clk);
              reg [7:0] q;
              always @(posedge clk) begin
                q = 8'd1;
              end
            endmodule
            """
        })
        assert "NO_BLOCKING_SEQUENTIAL" in {d["code"] for d in res_seq.diagnostics}

        # 2. Combinational block with blocking assignment -> NOT flagged
        res_comb = run_inline_lint_case({
            "top.sv": """
            module m(input [7:0] a, output reg [7:0] y);
              always @* begin
                y = a;
              end
            endmodule
            """
        })
        res_comb.expect_no_code("NO_BLOCKING_SEQUENTIAL")

        # 3. Task declaration with blocking assignment -> NOT flagged inside the task body
        res_task = run_inline_lint_case({
            "top.sv": """
            module m(input clk);
              reg [7:0] q;
              task automatic update_q();
                q = 8'd1;
              endtask
              always @(posedge clk) begin
                update_q();
              end
            endmodule
            """
        })
        # Document current behavior: task body is not inside ContextFlag.ALWAYS
        res_task.expect_no_code("NO_BLOCKING_SEQUENTIAL")


    def test_task_formal_input_direction_records_caller_argument_as_read(self):
        """Passing an identifier to a task input formal records a read event on that identifier."""
        source = """
        module m;
          reg [7:0] data;
          task automatic consume(input [7:0] in_data);
            $display("%d", in_data);
          endtask
          initial begin
            data = 8'd10;
            consume(data);
          end
        endmodule
        """
        tree, symbol_table = _analyze_source(source)
        module_scope = symbol_table.lookup_module("m")
        data_sym = module_scope.lookup("data")
        assert data_sym.is_written
        assert data_sym.read_count >= 1

    @pytest.mark.xfail(
        reason="Item 2.6: Inter-procedural task formal output direction propagation to caller arguments"
    )
    def test_task_formal_output_direction_marks_caller_variable_as_written(self):
        """When a caller passes a variable to a task output formal, inter-procedural analysis
        should record a write on the caller variable to prevent false positive READ_BEFORE_WRITE."""
        source = """
        module m;
          reg [7:0] data;
          reg [7:0] result;
          task automatic produce(output reg [7:0] out_data);
            out_data = 8'h55;
          endtask
          initial begin
            produce(data);
            result = data;
          end
        endmodule
        """
        tree, symbol_table = _analyze_source(source)
        module_scope = symbol_table.lookup_module("m")
        data_sym = module_scope.lookup("data")
        # Currently data is recorded as read-only at the call site produce(data)
        # When Item 2.6 is implemented, data.is_written will be True
        assert data_sym.is_written, "Task output argument should be recorded as a write on actual parameter"

        rbw = ReadBeforeWriteRule()
        diags = rbw.run(symbol_table)
        assert not any(d["code"] == "READ_BEFORE_WRITE" and "data" in d["message"] for d in diags)
