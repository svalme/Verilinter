// Breadth test suite for NO_IF_WITHOUT_BEGIN_END
// Category: maintainability_and_complexity
//
// Tests detection of procedural `if` branches containing single statements
// not wrapped in begin/end blocks, contrasting with properly wrapped blocks,
// else-if branches, function-local conditionals, and generate-level if statements.

// breadth: reports | Single statement in combinational if branch not wrapped in begin-end is reported.
// pair: p1
module unwrapped_combinational_if (
    input  wire a,
    output reg  y
);
  always_comb begin
    if (a)
      y = 1'b1; // Unwrapped single statement
  end
endmodule

// breadth: clean | Combinational if branch wrapped in begin-end block is not reported.
// pair: p1
module wrapped_combinational_if (
    input  wire a,
    output reg  y
);
  always_comb begin
    if (a) begin
      y = 1'b1;
    end
  end
endmodule

// breadth: reports | Sequential always_ff if branch not wrapped in begin-end is reported.
// pair: p2
module unwrapped_sequential_if (
    input  wire clk,
    input  wire en,
    input  wire d,
    output reg  q
);
  always_ff @(posedge clk) begin
    if (en)
      q <= d; // Unwrapped single statement in sequential block
  end
endmodule

// breadth: clean | Sequential always_ff if branch wrapped in begin-end is not reported.
// pair: p2
module wrapped_sequential_if (
    input  wire clk,
    input  wire en,
    input  wire d,
    output reg  q
);
  always_ff @(posedge clk) begin
    if (en) begin
      q <= d;
    end
  end
endmodule

// breadth: reports | Unwrapped branch in an else-if conditional statement is reported.
// pair: p3
module unwrapped_elseif_branch (
    input  wire a,
    input  wire b,
    output reg  [1:0] y
);
  always_comb begin
    if (a) begin
      y = 2'd1;
    end else if (b)
      y = 2'd2; // Unwrapped branch in else-if conditional
  end
endmodule

// breadth: clean | Wrapped branch in an else-if conditional statement is not reported.
// pair: p3
module wrapped_elseif_branch (
    input  wire a,
    input  wire b,
    output reg  [1:0] y
);
  always_comb begin
    if (a) begin
      y = 2'd1;
    end else if (b) begin
      y = 2'd2;
    end
  end
endmodule

// breadth: clean | Generate-level if without begin-end is not reported by procedural NO_IF_WITHOUT_BEGIN_END.
// pair: p4
module unwrapped_generate_if #(
    parameter int P = 0
);
  // Generate if is handled by generate rules, not procedural NO_IF_WITHOUT_BEGIN_END
  generate
    if (P == 0)
      wire sig_a;
  endgenerate
endmodule

// breadth: reports | Function body if branch not wrapped in begin-end is reported.
// pair: p4
module unwrapped_if_in_function (
    input  wire [7:0] in_val,
    output wire [7:0] out_val
);
  function automatic [7:0] compute(input [7:0] v);
    if (v != 8'h00)
      compute = v; // Unwrapped if in function body
    else
      compute = 8'hFF;
  endfunction

  assign out_val = compute(in_val);
endmodule

// breadth: clean | If statement with empty begin-end block is not reported.
module wrapped_empty_begin_end (
    input  wire a,
    output reg  y
);
  always_comb begin
    y = 1'b0;
    if (a) begin
      // Empty wrapped block
    end
  end
endmodule

// breadth: clean | Procedural case statement without if constructs is not reported.
module procedural_case_no_if (
    input  wire [1:0] sel,
    output reg        y
);
  always_comb begin
    case (sel)
      2'd0:    y = 1'b0;
      default: y = 1'b1;
    endcase
  end
endmodule
