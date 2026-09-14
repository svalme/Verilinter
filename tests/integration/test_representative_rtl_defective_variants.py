"""Controlled defective variants of the clean examples in
`test_representative_rtl_examples.py`. Starting from each clean example, change one behavior
at a time, verify the expected diagnostic fires with the correct code, count,
and source location, and verify that reverting the change restores the
original (clean, or documented-baseline) result.

Each defective source is a near-verbatim copy of its clean counterpart with
exactly one change; the diff is called out in each class's docstring rather
than left for the reader to spot.

## A note on "file" locations

These cases use `run_inline_lint_case`, which parses each snippet with
`pyslang.SyntaxTree.fromText(...)` and never gives pyslang a filename. Every
diagnostic's `"file"` therefore reads pyslang's default buffer name, `"source"`
-- not the dict key the case passes in -- regardless of single- or multi-file
input. That is a harness property, not something under test here, so `"file"`
is asserted only as the literal `"source"` throughout; `"line"`/`"col"` remain
meaningful per snippet.
"""

from tests.support.lint_harness import run_inline_lint_case
from .test_representative_rtl_examples import (
    CORRECTNESS_SELECTION,
    TestSequenceControllerFSMExample,
    TestTwoStagePipelineMultiModuleExample,
    TestUpCounterExample,
)


class TestUpCounterDuplicateNonblockingWriteVariant:
    """`up_counter` with one behavior changed: the enable branch gains a
    second, contradictory nonblocking write to `count` (a copy-paste-style
    bug -- e.g. a leftover decrement left in alongside the real increment)."""

    DEFECTIVE_SOURCE = """
`timescale 1ns/1ps

module up_counter #(
    parameter WIDTH = 8
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic             en,
    output logic [WIDTH-1:0] count
);

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      count <= '0;
    end else if (en) begin
      count <= count + 1'b1;
      count <= count - 1'b1;
    end
  end

endmodule
"""

    def test_duplicate_write_is_detected(self) -> None:
        result = run_inline_lint_case({"up_counter.sv": self.DEFECTIVE_SOURCE}, selection=CORRECTNESS_SELECTION)

        result.expect_codes({"NO_MULTIPLE_NONBLOCKING_WRITES"})
        diagnostic = result.expect_code_once("NO_MULTIPLE_NONBLOCKING_WRITES")
        # Location of the second (dead) write, `count <= count - 1'b1;`.
        assert diagnostic["line"] == 17
        assert diagnostic["col"] == 7
        assert diagnostic["file"] == "source"

    def test_removing_the_duplicate_write_restores_the_clean_result(self) -> None:
        result = run_inline_lint_case(
            {"up_counter.sv": TestUpCounterExample.SOURCE}, selection=CORRECTNESS_SELECTION
        )

        result.expect_codes(set())


class TestArithmeticDatapathParameterWidthBlindnessVariant:
    """`arithmetic_datapath` with one behavior changed: `product`'s declared
    width is narrowed from `2*WIDTH` to `WIDTH` bits, so the unsigned
    multiply's true `2*WIDTH`-bit result is silently truncated -- the classic
    "introduce a width mismatch" defect.

    `ARITHMETIC_RESULT_TRUNCATION` (and every other width/signedness rule built on
    `simple_expression_width_and_signed`/`Symbol.bit_width`) does not resolve a
    bit width that depends on a module parameter, because nothing elaborates
    parameter values into concrete widths, so this truncation produces zero
    diagnostics. `TestArithmeticDatapathLiteralWidthTruncationVariant` uses
    literal widths to show the rule works once a width is resolvable.
    """

    DEFECTIVE_SOURCE = """
`timescale 1ns/1ps

module arithmetic_datapath #(
    parameter WIDTH = 8
) (
    input  logic        signed [WIDTH-1:0] a,
    input  logic        signed [WIDTH-1:0] b,
    input  logic               [WIDTH-1:0] c,
    input  logic               [WIDTH-1:0] d,
    output logic         signed [WIDTH:0]  sum,
    output logic              [WIDTH-1:0] product
);

  assign sum = a + b;

  assign product = c * d;

endmodule
"""

    def test_narrowed_product_currently_produces_no_diagnostics(self) -> None:
        result = run_inline_lint_case(
            {"arithmetic_datapath.sv": self.DEFECTIVE_SOURCE}, selection=CORRECTNESS_SELECTION
        )

        result.expect_codes(set())

    def test_restoring_the_original_width_also_produces_no_diagnostics(self) -> None:
        from .test_representative_rtl_examples import TestArithmeticDatapathExample

        result = run_inline_lint_case(
            {"arithmetic_datapath.sv": TestArithmeticDatapathExample.SOURCE}, selection=CORRECTNESS_SELECTION
        )

        result.expect_codes(set())


class TestArithmeticDatapathLiteralWidthTruncationVariant:
    """A literal-width sibling of `arithmetic_datapath` (same shape: a signed
    add widened by one bit, an unsigned multiply), used instead of the
    parameterized clean example specifically because `Symbol.bit_width` is
    only ever resolvable for a literal port width -- see
    `TestArithmeticDatapathParameterWidthBlindnessVariant`. `product`'s width
    is narrowed from 16 to 8 bits, an actual truncation of the 8x8 multiply's
    true 16-bit result.
    """

    DEFECTIVE_SOURCE = """
`timescale 1ns/1ps

module arithmetic_datapath_literal_width (
    input  logic        signed [7:0] a,
    input  logic        signed [7:0] b,
    input  logic               [7:0] c,
    input  logic               [7:0] d,
    output logic         signed [8:0] sum,
    output logic               [7:0] product
);

  assign sum = a + b;

  assign product = c * d;

endmodule
"""

    FIXED_SOURCE = """
`timescale 1ns/1ps

module arithmetic_datapath_literal_width (
    input  logic        signed [7:0] a,
    input  logic        signed [7:0] b,
    input  logic               [7:0] c,
    input  logic               [7:0] d,
    output logic         signed [8:0] sum,
    output logic               [15:0] product
);

  assign sum = a + b;

  assign product = c * d;

endmodule
"""

    def test_truncated_multiply_is_detected(self) -> None:
        result = run_inline_lint_case(
            {"arithmetic_datapath_literal_width.sv": self.DEFECTIVE_SOURCE}, selection=CORRECTNESS_SELECTION
        )

        result.expect_codes({"ARITHMETIC_RESULT_TRUNCATION"})
        diagnostic = result.expect_code_once("ARITHMETIC_RESULT_TRUNCATION")
        assert diagnostic["line"] == 14
        assert diagnostic["col"] == 10
        assert diagnostic["file"] == "source"

    def test_widening_product_restores_the_clean_result(self) -> None:
        result = run_inline_lint_case(
            {"arithmetic_datapath_literal_width.sv": self.FIXED_SOURCE}, selection=CORRECTNESS_SELECTION
        )

        result.expect_codes(set())


class TestSequenceControllerMissingDefaultVariant:
    """`sequence_controller` with one behavior changed: the state `case`'s
    `default` case item is removed, leaving `state`'s behavior on an
    out-of-range value undefined.

    Deliberately checks both codes this fires: `MISSING_DEFAULT_ON_STATE_CASE`
    declares `NO_DEFAULT_CASE_STATEMENT` in `overlaps_with` for exactly this
    shape (a state-register case missing its default always co-fires the
    general case-default check alongside the state-specific one), and both are
    exercised together in `tests/test_rule_overlap_harness.py` -- this covers
    the "include any intentional companion diagnostics" case.
    """

    DEFECTIVE_SOURCE = """
`timescale 1ns/1ps

module sequence_controller (
    input  logic clk,
    input  logic rst_n,
    input  logic start,
    input  logic work_done,
    output logic busy,
    output logic done
);

  localparam logic [1:0] IDLE = 2'b00;
  localparam logic [1:0] LOAD = 2'b01;
  localparam logic [1:0] RUN = 2'b10;
  localparam logic [1:0] DONE_ST = 2'b11;

  logic [1:0] state;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE;
    end else begin
      case (state)
        IDLE: begin
          if (start) begin
            state <= LOAD;
          end else begin
            state <= IDLE;
          end
        end
        LOAD: begin
          state <= RUN;
        end
        RUN: begin
          if (work_done) begin
            state <= DONE_ST;
          end else begin
            state <= RUN;
          end
        end
        DONE_ST: begin
          state <= IDLE;
        end
      endcase
    end
  end

  assign busy = (state == LOAD) || (state == RUN);
  assign done = (state == DONE_ST);

endmodule
"""

    def test_missing_default_is_detected_with_its_companion_diagnostic(self) -> None:
        result = run_inline_lint_case(
            {"sequence_controller.sv": self.DEFECTIVE_SOURCE}, selection=CORRECTNESS_SELECTION
        )

        result.expect_codes({"MISSING_DEFAULT_ON_STATE_CASE", "NO_DEFAULT_CASE_STATEMENT"})
        # Both rules key off the same `endcase` token, so they share a location.
        for code in ("MISSING_DEFAULT_ON_STATE_CASE", "NO_DEFAULT_CASE_STATEMENT"):
            diagnostic = result.expect_code_once(code)
            assert diagnostic["line"] == 44
            assert diagnostic["col"] == 7
            assert diagnostic["file"] == "source"

    def test_restoring_the_default_case_restores_the_clean_result(self) -> None:
        result = run_inline_lint_case(
            {"sequence_controller.sv": TestSequenceControllerFSMExample.SOURCE}, selection=CORRECTNESS_SELECTION
        )

        result.expect_codes(set())


class TestTwoStagePipelineDisconnectedPortVariant:
    """The two-file `two_stage_pipeline`/`data_register` example with one
    behavior changed: `u_stage2`'s `.rst_n(rst_n)` connection is dropped,
    leaving that instance's reset port unconnected -- the "disconnect a
    required port" defect.

    `data_register` is unchanged; only `two_stage_pipeline`'s second instance
    loses its `rst_n` connection line. The clean example
    (`TestTwoStagePipelineMultiModuleExample`) produces zero diagnostics, so
    this variant's expected result is exactly one new
    `NO_UNCONNECTED_INSTANCE_PORTS` and nothing else.
    """

    DEFECTIVE_PIPELINE = """
`timescale 1ns/1ps

module two_stage_pipeline (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [7:0] data_out
);

  logic [7:0] stage1_q;

  data_register u_stage1 (
      .clk  (clk),
      .rst_n(rst_n),
      .d    (data_in),
      .q    (stage1_q)
  );

  data_register u_stage2 (
      .clk  (clk),
      .d    (stage1_q),
      .q    (data_out)
  );

endmodule
"""

    def test_disconnected_reset_port_is_detected(self) -> None:
        result = run_inline_lint_case(
            {
                "data_register.sv": TestTwoStagePipelineMultiModuleExample.DATA_REGISTER,
                "two_stage_pipeline.sv": self.DEFECTIVE_PIPELINE,
            },
            selection=CORRECTNESS_SELECTION,
        )

        result.expect_codes({"NO_UNCONNECTED_INSTANCE_PORTS"})
        diagnostic = result.expect_code_once("NO_UNCONNECTED_INSTANCE_PORTS")
        assert diagnostic["line"] == 19
        assert diagnostic["col"] == 3
        assert diagnostic["file"] == "source"
        result.expect_message_contains("NO_UNCONNECTED_INSTANCE_PORTS", "rst_n")

    def test_reconnecting_the_reset_port_restores_the_clean_result(self) -> None:
        result = run_inline_lint_case(
            {
                "data_register.sv": TestTwoStagePipelineMultiModuleExample.DATA_REGISTER,
                "two_stage_pipeline.sv": TestTwoStagePipelineMultiModuleExample.TWO_STAGE_PIPELINE,
            },
            selection=CORRECTNESS_SELECTION,
        )

        result.expect_codes(set())
