// Breadth test suite for NO_INSIDE_OPERATOR
// Category: operators_and_expressions
//
// Tests detection of the inside set-membership operator (expr inside { ... }),
// contrasting with explicit equality comparisons and case statements.

// breadth: reports | Standalone inside operator expression in continuous assignment is reported.
// pair: inside_op_vs_equality
module m(input [3:0] s, output wire y);
  assign y = s inside {4'd1, 4'd2};
endmodule

// breadth: clean | Explicit equality comparison is not reported.
// pair: inside_op_vs_equality
module m(input [3:0] s, output wire y);
  assign y = (s == 4'd1) || (s == 4'd2);
endmodule

// breadth: clean | Word inside inside comments is not reported.
module m;
  // s inside {1, 2}
  wire w = 1'b0;
endmodule

// breadth: reports | Inside operator expression with range in procedural conditional is reported.
module m(input [3:0] s, output reg y);
  always_comb begin
    if (s inside {[4'd0:4'd7]})
      y = 1'b1;
    else
      y = 1'b0;
  end
endmodule

// breadth: reports | Multiple inside operator expressions trigger multiple reports.
// expect: 2
module m(input [3:0] a, b, output wire y1, y2);
  assign y1 = a inside {4'd0};
  assign y2 = b inside {4'd1};
endmodule

// breadth: clean | Standard case statement without inside is not reported.
module m(input [3:0] s, output reg y);
  always_comb begin
    case (s)
      4'd1:    y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule
