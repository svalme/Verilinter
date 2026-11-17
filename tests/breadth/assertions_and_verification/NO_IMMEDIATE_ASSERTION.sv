// Breadth test suite for NO_IMMEDIATE_ASSERTION
// Category: assertions_and_verification
//
// Tests detection of immediate assertion statements (assert, assume, cover),
// contrasting with procedural conditionals and concurrent assertions.

// breadth: reports | Immediate assert statement in procedural block is reported.
// pair: immediate_vs_if_condition
module m(input a);
  initial begin
    assert (a);
  end
endmodule

// breadth: clean | Procedural if condition check is not reported.
// pair: immediate_vs_if_condition
module m(input a, output reg err);
  initial begin
    if (!a) err = 1'b1;
  end
endmodule

// breadth: clean | Words assert and assume inside comments are not reported.
module m;
  // assert (a) assume (b)
  wire w = 1'b0;
endmodule

// breadth: reports | Immediate assume statement is reported.
module m(input a);
  initial begin
    assume (a);
  end
endmodule

// breadth: reports | Multiple immediate assertions trigger multiple reports.
// expect: 2
module m(input a, b);
  always_comb begin
    assert (a);
    cover  (b);
  end
endmodule

// breadth: clean | Concurrent assert property is not reported by NO_IMMEDIATE_ASSERTION.
module m(input clk, a);
  assert property (@(posedge clk) a);
endmodule

// breadth: clean | Concurrent assertion statement instead of immediate assertion
module b_clean_neighbor_concurrent (input logic clk, req, ack);
    assert property (@(posedge clk) req |-> ack);
endmodule
