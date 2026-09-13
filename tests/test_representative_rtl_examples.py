"""Representative, complete RTL examples run through the real application flow
(parser -> walker -> rule runners via `tests/support/lint_harness.py`), rather
than the single-construct snippets most rule-specific test files use.

Existing rule tests are good at proving one construct is recognized in
isolation; they say little about how the supported constructs interact in a
realistic module (resets alongside arithmetic, an FSM alongside its outputs, a
signal wired between two instances).

## Rule selection

Every example below is checked against `CORRECTNESS_SELECTION`, not the full
"all" rule set. This project's naming/style rules (`rtl_style`/`module_style`
categories -- casing, port-direction suffixes, instance-name prefixes, etc.)
are intentionally always-on policy checks a team can disable per its own
convention (see `--category` in `docs/CLI.md`); they are orthogonal to whether
the RTL is *correct*, and at least one pair of them structurally cannot both
be satisfied at once for a clock **input** port (`PORT_DIRECTION_SUFFIX` wants
an `_i` suffix; `CLOCK_SIGNAL_NAMING` wants exactly `clk` or an `_clk`
suffix). `CORRECTNESS_SELECTION` scopes down to the `rtl_correctness`,
`semantic_correctness`, and `module_correctness` categories (real bugs), plus
`classic_rtl_exclusion`/`rtl_subset`/`sv_subset` (construct-usage policy for
this project's restricted RTL subset -- inert for any example that simply
doesn't use a banned legacy/simulation/SV-only construct), under the
`rtl_strict` profile specifically: `rtl_strict` is the only built-in profile
that permits the modern `always_ff`/`always_comb` procedural block keywords
these examples use (`sv_rtl_subset` bans `always_ff`/`always_latch` outright,
favoring plain `always`).

Each example also satisfies the two style-flavored checks folded into the
`rtl_subset` category (`MISSING_TIMESCALE_DIRECTIVE`, `NO_IF_WITHOUT_BEGIN_END`
/`NO_ELSE_WITHOUT_BEGIN_END`) directly in the RTL itself (a leading
`` `timescale `` directive, `begin`/`end` on every branch) rather than by
excluding them -- trivial to satisfy and arguably better practice for a
teaching example regardless.
"""

from src.pkg.rules.rule_selection import RuleSelection

from .support.lint_harness import run_inline_lint_case

CORRECTNESS_SELECTION = RuleSelection(
    enabled_categories=frozenset(
        {
            "rtl_correctness",
            "semantic_correctness",
            "module_correctness",
            "classic_rtl_exclusion",
            "rtl_subset",
            "sv_subset",
        }
    ),
    enabled_profiles=frozenset({"rtl_strict"}),
)


class TestUpCounterExample:
    """A counter with async active-low reset and an enable, the base case for
    "sequential logic with reset" this plan calls for."""

    SOURCE = """
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
    end
  end

endmodule
"""

    def test_produces_no_correctness_diagnostics(self) -> None:
        result = run_inline_lint_case({"up_counter.sv": self.SOURCE}, selection=CORRECTNESS_SELECTION)

        result.expect_codes(set())


class TestArithmeticDatapathExample:
    """A small combinational datapath with explicit widths and signedness: a
    signed add widened by one bit and an unsigned multiply widened to the full
    product width, both wide enough that `ARITHMETIC_RESULT_TRUNCATION` (which
    deliberately ignores the add/subtract carry-out bit, matching Verilog's own
    self-determined-width rule) has nothing to flag either way."""

    SOURCE = """
`timescale 1ns/1ps

module arithmetic_datapath #(
    parameter WIDTH = 8
) (
    input  logic        signed [WIDTH-1:0] a,
    input  logic        signed [WIDTH-1:0] b,
    input  logic               [WIDTH-1:0] c,
    input  logic               [WIDTH-1:0] d,
    output logic         signed [WIDTH:0]  sum,
    output logic              [2*WIDTH-1:0] product
);

  // Widened by one bit so a signed add can never overflow its result.
  assign sum = a + b;

  // Widened to the full 2*WIDTH product width so an unsigned multiply
  // can never overflow its result.
  assign product = c * d;

endmodule
"""

    def test_produces_no_correctness_diagnostics(self) -> None:
        result = run_inline_lint_case({"arithmetic_datapath.sv": self.SOURCE}, selection=CORRECTNESS_SELECTION)

        result.expect_codes(set())


class TestSequenceControllerFSMExample:
    """A one-process FSM controller (the only style the `fsms` rule category
    recognizes -- see `src/pkg/parser/_syntax_queries/fsm.py`): a state
    register nonblocking-assigned inside the same edge-sensitive block as the
    `case` that reads it, async-reset-covered, with a `default` case item.

    Deliberately binary-encoded (2-bit state, 4 states): `ONE_HOT_ENCODING_
    VIOLATION` only applies when the declared width equals the distinct state
    count (3+ states) -- 2 bits for 4 states is ordinary binary encoding, not
    a one-hot-intent shape, so it correctly does not apply here.
    """

    SOURCE = """
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
        default: begin
          state <= IDLE;
        end
      endcase
    end
  end

  assign busy = (state == LOAD) || (state == RUN);
  assign done = (state == DONE_ST);

endmodule
"""

    def test_produces_no_correctness_diagnostics(self) -> None:
        result = run_inline_lint_case({"sequence_controller.sv": self.SOURCE}, selection=CORRECTNESS_SELECTION)

        result.expect_codes(set())


class TestTwoStagePipelineMultiModuleExample:
    """A small two-file, two-module design: `two_stage_pipeline` instantiates
    `data_register` twice, chained through an internal signal (`stage1_q`) --
    meaningful port connections, in the sense that
    removing either instance or connection changes the design's behavior.

    This is expected to produce zero diagnostics: this module is a completely
    ordinary two-stage pipeline.
    `IdentifierNameHandler` records an identifier used inside an instance
    port-connection expression as a plain read regardless of which side of the
    connection actually drives the net (the connected module's port direction
    generally isn't resolvable from a single-file walk), so `NO_UNDRIVEN_SIGNAL`,
    `NO_UNDRIVEN_OUTPUT_PORT`, `READ_BEFORE_WRITE`, and `UNREAD_INSTANCE_OUTPUT`
    each skip a signal recorded as used inside a port connection
    (`Symbol.is_used_in_port_connection`) and, for `UNREAD_INSTANCE_OUTPUT`, a
    signal that is itself an output/inout port -- see
    `enclosing_port_connection`'s docstring.
    """

    DATA_REGISTER = """
`timescale 1ns/1ps

module data_register (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] d,
    output logic [7:0] q
);

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      q <= '0;
    end else begin
      q <= d;
    end
  end

endmodule
"""

    TWO_STAGE_PIPELINE = """
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
      .rst_n(rst_n),
      .d    (stage1_q),
      .q    (data_out)
  );

endmodule
"""

    def test_produces_no_diagnostics(self) -> None:
        result = run_inline_lint_case(
            {
                "data_register.sv": self.DATA_REGISTER,
                "two_stage_pipeline.sv": self.TWO_STAGE_PIPELINE,
            },
            selection=CORRECTNESS_SELECTION,
        )

        result.expect_codes(set())
