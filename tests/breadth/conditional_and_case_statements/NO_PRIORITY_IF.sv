// Breadth test suite for NO_PRIORITY_IF
// Category: conditional_and_case_statements
//
// Tests detection of priority if statements,
// contrasting with standard unadorned if statements and unique if statements.

// breadth: reports | Priority if statement is reported.
// pair: priority_if_vs_standard_if
module m(input a, output reg y);
  always_comb begin
    priority if (a) y = 1'b1;
    else            y = 1'b0;
  end
endmodule

// breadth: clean | Standard if-else statement without qualifier is not reported.
// pair: priority_if_vs_standard_if
module m(input a, output reg y);
  always_comb begin
    if (a) y = 1'b1;
    else   y = 1'b0;
  end
endmodule

// breadth: clean | Word priority inside comments is not reported.
module m;
  // priority if
  wire w = 1'b0;
endmodule

// breadth: reports | Priority if inside sequential block is reported.
module m(input clk, a, output reg q);
  always_ff @(posedge clk) begin
    priority if (a) q <= 1'b1;
    else            q <= 1'b0;
  end
endmodule

// breadth: reports | Multiple priority if statements trigger multiple reports.
// expect: 2
module m(input a, b, output reg y1, y2);
  always_comb begin
    priority if (a) y1 = 1'b1;
    else            y1 = 1'b0;
    priority if (b) y2 = 1'b1;
    else            y2 = 1'b0;
  end
endmodule

// breadth: clean | Unique if statement is clean for NO_PRIORITY_IF.
module m(input a, output reg y);
  always_comb begin
    unique if (a) y = 1'b1;
    else          y = 1'b0;
  end
endmodule
