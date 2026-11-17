// Breadth test suite for NO_CASE_INSIDE
// Category: conditional_and_case_statements
//
// Tests detection of case statements using the inside keyword (case ... inside),
// contrasting with standard case statements and the standalone inside operator.

// breadth: reports | Case statement with inside keyword is reported.
// pair: case_inside_vs_standard_case
module m(input [3:0] s, output reg y);
  always_comb begin
    case (s) inside
      [4'd0:4'd3]: y = 1'b1;
      default:     y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Standard case statement with explicit comma-separated items is not reported.
// pair: case_inside_vs_standard_case
module m(input [3:0] s, output reg y);
  always_comb begin
    case (s)
      4'd0, 4'd1, 4'd2, 4'd3: y = 1'b1;
      default:                y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Words case inside inside comments are not reported.
module m;
  // case inside
  wire w = 1'b0;
endmodule

// breadth: reports | Case inside statement inside a function is reported.
module m;
  function automatic logic check_range(input [3:0] val);
    case (val) inside
      [4'd0:4'd7]: check_range = 1'b1;
      default:     check_range = 1'b0;
    endcase
  endfunction
endmodule

// breadth: reports | Multiple case inside statements trigger multiple reports.
// expect: 2
module m(input [3:0] a, b, output reg y1, y2);
  always_comb begin
    case (a) inside
      default: y1 = 1'b0;
    endcase
    case (b) inside
      default: y2 = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Standalone inside operator in continuous assign is not reported by NO_CASE_INSIDE.
module m(input [3:0] s, output wire y);
  assign y = s inside {4'd1, 4'd2};
endmodule
