// Breadth test suite for MISSING_GENERATE_BLOCK_LABEL
// Category: parameters_and_generate_logic
//
// Tests detection of generate blocks (GenerateBlockNode) missing an explicit
// label on the begin keyword, covering if-generate, case-generate, loop-generate,
// and bare generate blocks, contrasting with properly labeled generate blocks and unwrapped constructs.

// breadth: reports | Generate-if begin block missing a label is reported.
// pair: p1
module unlabeled_generate_if #(
    parameter int COND = 1
);
  generate
    if (COND == 1) begin
      wire active_sig;
    end
  endgenerate
endmodule

// breadth: clean | Generate-if begin block with explicit label gen_active is not reported.
// pair: p1
module labeled_generate_if #(
    parameter int COND = 1
);
  generate
    if (COND == 1) begin : gen_active
      wire active_sig;
    end
  endgenerate
endmodule

// breadth: reports | Generate-else begin block missing a label is reported.
// pair: p2
module unlabeled_generate_else #(
    parameter int COND = 0
);
  generate
    if (COND == 1) begin : gen_main
      wire sig_a;
    end else begin // Missing label on else branch
      wire sig_b;
    end
  endgenerate
endmodule

// breadth: clean | Generate-else begin block with explicit label gen_alt is not reported.
// pair: p2
module labeled_generate_else #(
    parameter int COND = 0
);
  generate
    if (COND == 1) begin : gen_main
      wire sig_a;
    end else begin : gen_alt
      wire sig_b;
    end
  endgenerate
endmodule

// breadth: reports | Generate-case item begin block missing a label is reported.
// pair: p3
module unlabeled_generate_case_item #(
    parameter int SEL = 0
);
  generate
    case (SEL)
      0: begin
        wire sel_zero;
      end
      default: begin : gen_def
        wire sel_default;
      end
    endcase
  endgenerate
endmodule

// breadth: clean | Generate-case item begin blocks with explicit labels are not reported.
// pair: p3
module labeled_generate_case_item #(
    parameter int SEL = 0
);
  generate
    case (SEL)
      0: begin : gen_zero
        wire sel_zero;
      end
      default: begin : gen_def
        wire sel_default;
      end
    endcase
  endgenerate
endmodule

// breadth: reports | Generate-for loop begin block missing a label is reported.
// pair: p4
module unlabeled_generate_for #(
    parameter int N = 4
);
  generate
    for (genvar i = 0; i < N; i = i + 1) begin
      wire lane_bit;
    end
  endgenerate
endmodule

// breadth: clean | Generate-for loop begin block with explicit label gen_lanes is not reported.
// pair: p4
module labeled_generate_for #(
    parameter int N = 4
);
  generate
    for (genvar i = 0; i < N; i = i + 1) begin : gen_lanes
      wire lane_bit;
    end
  endgenerate
endmodule

// breadth: reports | Bare generate begin block missing a label is reported.
// pair: p5
module unlabeled_bare_generate_block;
  generate
    begin
      wire data_wire;
    end
  endgenerate
endmodule

// breadth: clean | Bare generate begin block with explicit label gen_bare is not reported.
// pair: p5
module labeled_bare_generate_block;
  generate
    begin : gen_bare
      wire data_wire;
    end
  endgenerate
endmodule

// breadth: clean | Unwrapped single-statement generate body without begin-end does not create a block and is not reported.
module unwrapped_generate_no_block #(
    parameter int COND = 1
);
  // Single-statement generate body without begin/end does not create GenerateBlockNode
  generate
    if (COND == 1)
      wire standalone_sig;
  endgenerate
endmodule

// breadth: clean | Procedural begin-end block is not a generate block and is not reported.
module procedural_begin_end_clean (
    input  wire a,
    output reg  y
);
  // Procedural begin/end blocks are not GenerateBlockNode
  always_comb begin
    y = a;
  end
endmodule
