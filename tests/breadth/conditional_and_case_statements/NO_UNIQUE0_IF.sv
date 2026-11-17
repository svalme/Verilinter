// Breadth test suite for NO_UNIQUE0_IF
// Category: conditional_and_case_statements
//
// Tests detection of unique0 if statements,
// contrasting with standard if statements and unique if statements.

// breadth: reports | Unique0 if statement is reported.
// pair: unique0_if_vs_standard_if
module m(input a, output reg y);
  always_comb begin
    unique0 if (a) y = 1'b1;
    else           y = 1'b0;
  end
endmodule

// breadth: clean | Standard if-else statement without qualifier is not reported.
// pair: unique0_if_vs_standard_if
module m(input a, output reg y);
  always_comb begin
    if (a) y = 1'b1;
    else   y = 1'b0;
  end
endmodule

// breadth: clean | Word unique0 inside comments is not reported.
module m;
  // unique0 if
  wire w = 1'b0;
endmodule

// breadth: reports | Unique0 if inside sequential block is reported.
module m(input clk, a, output reg q);
  always_ff @(posedge clk) begin
    unique0 if (a) q <= 1'b1;
    else            q <= 1'b0;
  end
endmodule

// breadth: reports | Multiple unique0 if statements trigger multiple reports.
// expect: 2
module m(input a, b, output reg y1, y2);
  always_comb begin
    unique0 if (a) y1 = 1'b1;
    else           y1 = 1'b0;
    unique0 if (b) y2 = 1'b1;
    else           y2 = 1'b0;
  end
endmodule

// breadth: clean | Unique if statement without 0 is clean for NO_UNIQUE0_IF.
module m(input a, output reg y);
  always_comb begin
    unique if (a) y = 1'b1;
    else          y = 1'b0;
  end
endmodule
