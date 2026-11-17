// Breadth test suite for NO_CASEX_CASEZ
// Category: conditional_and_case_statements
//
// Tests detection of casex and casez statements,
// contrasting with standard masked case statements and comments.

// breadth: reports | Statement using casez is reported.
// pair: casez_vs_case
module m(input [1:0] s, output reg y);
  always_comb begin
    casez (s)
      2'b1?:   y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Standard case statement with bitwise mask is not reported.
// pair: casez_vs_case
module m(input [1:0] s, output reg y);
  always_comb begin
    case (s & 2'b10)
      2'b10:   y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Words casex and casez inside comments are not reported.
module m;
  // casex casez
  wire w = 1'b0;
endmodule

// breadth: reports | Statement using casex is reported.
module m(input [1:0] s, output reg y);
  always_comb begin
    casex (s)
      2'b1x:   y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: reports | Both casez and casex in the same module trigger multiple reports.
// expect: 2
module m(input [1:0] a, b, output reg y1, y2);
  always_comb begin
    casez (a)
      default: y1 = 1'b0;
    endcase
    casex (b)
      default: y2 = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Standard case statement is clean for NO_CASEX_CASEZ.
module m(input [1:0] s, output reg y);
  always_comb begin
    case (s)
      2'd0:    y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule
