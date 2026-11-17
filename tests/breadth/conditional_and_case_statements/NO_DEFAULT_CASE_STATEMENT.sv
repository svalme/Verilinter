// Breadth test suite for NO_DEFAULT_CASE_STATEMENT
// Category: conditional_and_case_statements
//
// Tests detection of procedural case statements missing a default branch,
// contrasting with procedural cases having default branches, casez/casex variants,
// unique/priority qualifiers, function-local cases, and empty default branches.

// breadth: reports | Procedural case statement in always_comb missing a default branch is reported.
// pair: p1
module procedural_case_missing_default (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    case (sel)
      2'd0: y = 1'b0;
      2'd1: y = 1'b1;
    endcase
  end
endmodule

// breadth: clean | Procedural case statement with default branch is not reported.
// pair: p1
module procedural_case_with_default (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    case (sel)
      2'd0:    y = 1'b0;
      2'd1:    y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | Procedural casez statement missing a default branch is reported.
// pair: p2
module procedural_casez_missing_default (
    input  wire [3:0] opcode,
    output reg        valid
);
  always_comb begin
    casez (opcode)
      4'b1???: valid = 1'b1;
      4'b01??: valid = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Procedural casez statement with default branch is not reported.
// pair: p2
module procedural_casez_with_default (
    input  wire [3:0] opcode,
    output reg        valid
);
  always_comb begin
    casez (opcode)
      4'b1???: valid = 1'b1;
      4'b01??: valid = 1'b0;
      default: valid = 1'b0;
    endcase
  end
endmodule

// breadth: reports | Unique case statement missing a default branch is reported.
// pair: p3
module unique_case_missing_default (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    unique case (sel)
      2'd0: y = 1'b0;
      2'd1: y = 1'b1;
    endcase
  end
endmodule

// breadth: clean | Unique case statement with default branch is not reported.
// pair: p3
module unique_case_with_default (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    unique case (sel)
      2'd0:    y = 1'b0;
      2'd1:    y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | Function-local case statement missing a default branch is reported.
// pair: p4
module function_case_missing_default (
    input  wire [1:0] in_code,
    output wire [3:0] out_val
);
  function automatic [3:0] decode(input [1:0] c);
    case (c)
      2'd0: decode = 4'h1;
      2'd1: decode = 4'h2;
    endcase
  endfunction

  assign out_val = decode(in_code);
endmodule

// breadth: clean | Function-local case statement with default branch is not reported.
// pair: p4
module function_case_with_default (
    input  wire [1:0] in_code,
    output wire [3:0] out_val
);
  function automatic [3:0] decode(input [1:0] c);
    case (c)
      2'd0:    decode = 4'h1;
      2'd1:    decode = 4'h2;
      default: decode = 4'h0;
    endcase
  endfunction

  assign out_val = decode(in_code);
endmodule

// breadth: reports | Exhaustive case statement covering all input combinations without default is reported.
// pair: p5
module complete_case_missing_default (
    input  wire [1:0] sel,
    output reg  [1:0] y
);
  // Covers all 4 possible values of 2-bit sel, but rule still requires default
  always_comb begin
    case (sel)
      2'd0: y = 2'd0;
      2'd1: y = 2'd1;
      2'd2: y = 2'd2;
      2'd3: y = 2'd3;
    endcase
  end
endmodule

// breadth: clean | Procedural case statement with default branch placed first is not reported.
// pair: p5
module default_not_last (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    case (sel)
      default: y = 1'b0;
      2'd0:    y = 1'b1;
    endcase
  end
endmodule

// breadth: clean | Procedural case statement with null empty default statement is not reported.
module empty_default_statement (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    case (sel)
      2'd0:    y = 1'b1;
      default: ;
    endcase
  end
endmodule

// breadth: clean | Generate-level case is not reported by NO_DEFAULT_CASE_STATEMENT (handled by DEFAULT_CASE).
module generate_case_clean_for_procedural_rule #(
    parameter int P = 0
);
  // Generate-level case is handled by DEFAULT_CASE, not NO_DEFAULT_CASE_STATEMENT
  case (P)
    0: wire a;
    1: wire b;
  endcase
endmodule
