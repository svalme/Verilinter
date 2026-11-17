// Breadth test suite for NO_ELSE_WITHOUT_BEGIN_END
// Category: maintainability_and_complexity
//
// Tests detection of procedural `else` branches containing single statements
// not wrapped in begin/end blocks, contrasting with properly wrapped else blocks,
// chained else-if statements, conditionals without else branches, and generate-level constructs.

// breadth: reports | Single statement in combinational else branch not wrapped in begin-end is reported.
// pair: p1
module unwrapped_combinational_else (
    input  wire a,
    output reg  y
);
  always_comb begin
    if (a) begin
      y = 1'b1;
    end else
      y = 1'b0; // Unwrapped else branch
  end
endmodule

// breadth: clean | Combinational else branch wrapped in begin-end block is not reported.
// pair: p1
module wrapped_combinational_else (
    input  wire a,
    output reg  y
);
  always_comb begin
    if (a) begin
      y = 1'b1;
    end else begin
      y = 1'b0;
    end
  end
endmodule

// breadth: reports | Sequential always_ff else branch not wrapped in begin-end is reported.
// pair: p2
module unwrapped_sequential_else (
    input  wire clk,
    input  wire en,
    input  wire d,
    output reg  q
);
  always_ff @(posedge clk) begin
    if (en) begin
      q <= d;
    end else
      q <= 1'b0; // Unwrapped else in sequential block
  end
endmodule

// breadth: clean | Sequential always_ff else branch wrapped in begin-end is not reported.
// pair: p2
module wrapped_sequential_else (
    input  wire clk,
    input  wire en,
    input  wire d,
    output reg  q
);
  always_ff @(posedge clk) begin
    if (en) begin
      q <= d;
    end else begin
      q <= 1'b0;
    end
  end
endmodule

// breadth: reports | Terminal else branch following an else-if not wrapped in begin-end is reported.
// pair: p3
module terminal_unwrapped_else_in_chain (
    input  wire a,
    input  wire b,
    output reg  [1:0] y
);
  always_comb begin
    if (a) begin
      y = 2'd1;
    end else if (b) begin
      y = 2'd2;
    end else
      y = 2'd3; // Terminal else not wrapped
  end
endmodule

// breadth: clean | Chained else-if branch is a conditional statement and is not reported as an unwrapped else.
// pair: p3
module chained_elseif_branch (
    input  wire a,
    input  wire b,
    output reg  [1:0] y
);
  always_comb begin
    if (a) begin
      y = 2'd1;
    end else if (b) begin
      // else if is a conditional statement, not an unwrapped terminal else
      y = 2'd2;
    end
  end
endmodule

// breadth: reports | Function body else branch not wrapped in begin-end is reported.
// pair: p4
module unwrapped_else_in_function (
    input  wire [7:0] in_val,
    output wire [7:0] out_val
);
  function automatic [7:0] compute(input [7:0] v);
    if (v != 8'h00) begin
      compute = v;
    end else
      compute = 8'h00; // Unwrapped else in function
  endfunction

  assign out_val = compute(in_val);
endmodule

// breadth: clean | Function body else branch wrapped in begin-end is not reported.
// pair: p4
module wrapped_else_in_function (
    input  wire [7:0] in_val,
    output wire [7:0] out_val
);
  function automatic [7:0] compute(input [7:0] v);
    if (v != 8'h00) begin
      compute = v;
    end else begin
      compute = 8'h00;
    end
  endfunction

  assign out_val = compute(in_val);
endmodule

// breadth: gap | Generate else wrapped in begin-end is falsely flagged because GenerateBlockSyntax is not recognized as block.
// expect: 0
module generate_else_wrapped #(
    parameter int P = 0
);
  // Generate else uses ElseClauseSyntax but its body is GenerateBlockSyntax,
  // which is currently not recognized by is_block_statement() in is_unwrapped_else_body().
  generate
    if (P == 0) begin : gen_a
      wire sig_a;
    end else begin : gen_b
      wire sig_b;
    end
  endgenerate
endmodule

// breadth: clean | Conditional if statement without an else branch is not reported.
module conditional_without_else (
    input  wire a,
    output reg  y
);
  always_comb begin
    y = 1'b0;
    if (a) begin
      y = 1'b1;
    end
  end
endmodule

// breadth: clean | Empty else branch wrapped in begin-end is not reported.
module wrapped_empty_else (
    input  wire a,
    output reg  y
);
  always_comb begin
    if (a) begin
      y = 1'b1;
    end else begin
      // Empty wrapped else block
    end
  end
endmodule
