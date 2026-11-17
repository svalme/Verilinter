// Breadth test suite for NO_UNIQUE0_CASE
// Category: conditional_and_case_statements
//
// Tests detection of unique0 case statements,
// contrasting with standard unadorned case statements and unique0 if statements.

// breadth: reports | Unique0 case statement is reported.
// pair: unique0_case_vs_standard_case
module m(input [1:0] s, output reg y);
  always_comb begin
    unique0 case (s)
      2'd0:    y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Standard case statement without qualifier is not reported.
// pair: unique0_case_vs_standard_case
module m(input [1:0] s, output reg y);
  always_comb begin
    case (s)
      2'd0:    y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Word unique0 inside comments is not reported.
module m;
  // unique0 case
  wire w = 1'b0;
endmodule

// breadth: reports | Unique0 case statement inside function is reported.
module m;
  function automatic logic decode(input [1:0] s);
    unique0 case (s)
      2'd0:    decode = 1'b1;
      default: decode = 1'b0;
    endcase
  endfunction
endmodule

// breadth: reports | Multiple unique0 case statements trigger multiple reports.
// expect: 2
module m(input [1:0] a, b, output reg y1, y2);
  always_comb begin
    unique0 case (a)
      default: y1 = 1'b0;
    endcase
    unique0 case (b)
      default: y2 = 1'b0;
    endcase
  end
endmodule

// breadth: clean | Unique0 if statement is clean for NO_UNIQUE0_CASE.
module m(input a, output reg y);
  always_comb begin
    unique0 if (a) y = 1'b1;
    else           y = 1'b0;
  end
endmodule
