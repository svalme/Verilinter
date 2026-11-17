// Breadth test suite for DEFAULT_CASE
// Category: conditional_and_case_statements
//
// Tests detection of generate-level case constructs (CASE_GENERATE) missing a
// default branch, contrasting with generate cases having default branches,
// default placed first, empty default statements, and procedural case statements.

// breadth: reports | Generate-level case construct missing a default branch is reported.
// pair: p1
module generate_case_missing_default #(
    parameter int WIDTH = 8
);
  case (WIDTH)
    8:  wire [7:0] data;
    16: wire [15:0] data;
  endcase
endmodule

// breadth: clean | Generate-level case construct with a default branch is not reported.
// pair: p1
module generate_case_with_default #(
    parameter int WIDTH = 8
);
  case (WIDTH)
    8:       wire [7:0] data;
    16:      wire [15:0] data;
    default: wire [31:0] data;
  endcase
endmodule

// breadth: reports | Explicit generate-block case construct missing a default branch is reported.
// pair: p2
module explicit_generate_case_no_default #(
    parameter int MODE = 0
);
  generate
    case (MODE)
      0: wire mode_a;
      1: wire mode_b;
    endcase
  endgenerate
endmodule

// breadth: clean | Explicit generate-block case construct with a default branch is not reported.
// pair: p2
module explicit_generate_case_with_default #(
    parameter int MODE = 0
);
  generate
    case (MODE)
      0:       wire mode_a;
      1:       wire mode_b;
      default: wire mode_default;
    endcase
  endgenerate
endmodule

// breadth: reports | Nested generate case within an if-generate branch missing a default branch is reported.
// pair: p3
module nested_generate_case_no_default #(
    parameter int A = 0,
    parameter int B = 1
);
  generate
    if (A == 0) begin : gen_outer
      case (B)
        0: wire sig_b0;
        1: wire sig_b1;
      endcase
    end
  endgenerate
endmodule

// breadth: clean | Nested generate case within an if-generate branch with a default branch is not reported.
// pair: p3
module nested_generate_case_with_default #(
    parameter int A = 0,
    parameter int B = 1
);
  generate
    if (A == 0) begin : gen_outer
      case (B)
        0:       wire sig_b0;
        default: wire sig_b_def;
      endcase
    end
  endgenerate
endmodule

// breadth: reports | Multi-expression item generate case missing a default branch is reported.
// pair: p4
module multi_item_generate_case_no_default #(
    parameter int SEL = 2
);
  case (SEL)
    0, 1: wire low_band;
    2, 3: wire high_band;
  endcase
endmodule

// breadth: clean | Generate-level case with default branch placed first is not reported.
// pair: p4
module generate_case_default_not_last #(
    parameter int SEL = 2
);
  case (SEL)
    default: wire any_band;
    0, 1:    wire low_band;
  endcase
endmodule

// breadth: clean | Generate-level case with null empty default statement is not reported.
module generate_case_empty_default #(
    parameter int SEL = 0
);
  case (SEL)
    0:       wire sig_zero;
    default: ;
  endcase
endmodule

// breadth: clean | Procedural case missing default is not reported by DEFAULT_CASE (handled by NO_DEFAULT_CASE_STATEMENT).
module procedural_case_not_reported_by_this_rule (
    input  wire [1:0] sel,
    output reg        out_val
);
  // Procedural case missing default is handled by NO_DEFAULT_CASE_STATEMENT
  always_comb begin
    case (sel)
      2'd0: out_val = 1'b0;
      2'd1: out_val = 1'b1;
    endcase
  end
endmodule

// breadth: clean | Generate if construct without case is not reported.
module generate_if_not_case #(
    parameter int P = 1
);
  generate
    if (P == 1) begin : gen_p1
      wire active;
    end
  endgenerate
endmodule
