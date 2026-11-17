// Breadth test suite for ASSIGNEQEXPR
// Category: operators_and_expressions
//
// Tests detection of assignment operators '=' used inside expressions (where '=='
// may have been intended or side-effecting assignment is embedded in expressions),
// contrasting with equality comparisons ('=='), statement-level assignments,
// and for-loop header assignments.

// breadth: reports | Assignment operator '=' embedded inside an if conditional expression is reported.
// pair: p1
module assignment_in_if_condition (
    input  wire a,
    output reg  x,
    output reg  y
);
  always_comb begin
    if ((x = a)) begin
      y = 1'b1;
    end else begin
      y = 1'b0;
    end
  end
endmodule

// breadth: clean | Equality operator '==' in if conditional expression is not reported.
// pair: p1
module equality_in_if_condition (
    input  wire a,
    input  wire x,
    output reg  y
);
  always_comb begin
    if (x == a) begin
      y = 1'b1;
    end else begin
      y = 1'b0;
    end
  end
endmodule

// breadth: reports | Assignment operator '=' embedded inside a ternary condition expression is reported.
// pair: p2
module assignment_in_ternary_condition (
    input  wire b,
    output wire d,
    output reg  e
);
  assign d = (e = 1'b1) ? 1'b1 : b;
endmodule

// breadth: clean | Equality comparison '==' in ternary condition expression is not reported.
// pair: p2
module equality_in_ternary_condition (
    input  wire b,
    input  wire e,
    output wire d
);
  assign d = (e == 1'b1) ? 1'b1 : b;
endmodule

// breadth: reports | Assignment operator '=' embedded inside another assignment expression RHS is reported.
// pair: p3
module nested_assignment_rhs (
    input  wire c,
    output reg  a,
    output reg  b
);
  always_comb begin
    a = (b = c);
  end
endmodule

// breadth: clean | Equality comparison '==' in assignment expression RHS is not reported.
// pair: p3
module equality_rhs_assignment (
    input  wire b,
    input  wire c,
    output reg  a
);
  always_comb begin
    a = (b == c);
  end
endmodule

// breadth: reports | Assignment operator '=' embedded inside while-loop condition expression is reported.
// pair: p4
module assignment_in_while_condition (
    input  wire clk,
    output reg  [3:0] cnt,
    output reg  [3:0] flag
);
  initial begin
    cnt = 4'd0;
    while ((flag = cnt)) begin
      cnt = cnt + 4'd1;
    end
  end
endmodule

// breadth: clean | Equality comparison '==' in while-loop condition expression is not reported.
// pair: p4
module equality_in_while_condition (
    input  wire clk,
    output reg  [3:0] cnt,
    input  wire [3:0] flag
);
  initial begin
    cnt = 4'd0;
    while (cnt == flag) begin
      cnt = cnt + 4'd1;
    end
  end
endmodule

// breadth: clean | Standalone statement-level blocking assignment is not reported.
module standalone_blocking_assignment (
    input  wire a,
    output reg  y
);
  always_comb begin
    y = a;
  end
endmodule

// breadth: clean | For-loop header initialization and step assignments are not reported.
module for_loop_header_assignments (
    input  wire [3:0] in_data,
    output reg  [3:0] out_data [0:3]
);
  always_comb begin
    for (int i = 0; i < 4; i = i + 1) begin
      out_data[i] = in_data;
    end
  end
endmodule

// breadth: clean | Standalone statement-level nonblocking assignment is not reported.
module nonblocking_assignment_statement (
    input  wire clk,
    input  wire d,
    output reg  q
);
  always_ff @(posedge clk) begin
    q <= d;
  end
endmodule
