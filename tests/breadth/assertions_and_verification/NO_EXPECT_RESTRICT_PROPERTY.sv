// Breadth test suite for NO_EXPECT_RESTRICT_PROPERTY
// Category: assertions_and_verification
//
// Tests detection of restrict property and procedural expect statements,
// contrasting with standard assert property, immediate assertions, and comments.

// breadth: reports | Restrict property statement is reported.
// pair: restrict_vs_assert
module m(input clk, a);
  restrict property (@(posedge clk) a);
endmodule

// breadth: clean | Standard concurrent assert property is not reported by this rule.
// pair: restrict_vs_assert
module m(input clk, a);
  assert property (@(posedge clk) a);
endmodule

// breadth: clean | Words expect and restrict inside comments are not reported.
module m;
  // expect restrict property
  wire w = 1'b0;
endmodule

// breadth: reports | Procedural expect statement is reported.
module m(input clk, a);
  initial begin
    expect (@(posedge clk) a);
  end
endmodule

// breadth: reports | Multiple restrict property statements trigger multiple reports.
// expect: 2
module m(input clk, a, b);
  restrict property (@(posedge clk) a);
  restrict property (@(posedge clk) b);
endmodule

// breadth: clean | Immediate assertion is clean for NO_EXPECT_RESTRICT_PROPERTY.
module m(input a);
  initial begin
    assert (a);
  end
endmodule
