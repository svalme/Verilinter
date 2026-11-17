// Breadth test suite for NO_CONCURRENT_ASSERTION
// Category: assertions_and_verification
//
// Tests detection of concurrent assertions (assert/assume/cover property),
// contrasting with procedural checks, immediate assertions, and comments.

// breadth: reports | Concurrent assert property statement is reported.
// pair: concurrent_vs_immediate
module m(input clk, a);
  assert property (@(posedge clk) a);
endmodule

// breadth: clean | Procedural if-statement condition check is not reported.
// pair: concurrent_vs_immediate
module m(input clk, a, output reg err);
  always_ff @(posedge clk) begin
    if (!a) err <= 1'b1;
  end
endmodule

// breadth: clean | Words assert property inside comments are not reported.
module m;
  // assert property
  wire w = 1'b0;
endmodule

// breadth: reports | Concurrent assume property statement is reported.
module m(input clk, a);
  assume property (@(posedge clk) a);
endmodule

// breadth: reports | Multiple concurrent assertions trigger multiple reports.
// expect: 2
module m(input clk, a, b);
  assert property (@(posedge clk) a);
  cover  property (@(posedge clk) b);
endmodule

// breadth: clean | Immediate assertion is clean for NO_CONCURRENT_ASSERTION.
module m(input a);
  initial begin
    assert (a);
  end
endmodule

// breadth: clean | Immediate assertion in procedural block instead of concurrent assertion
module b_clean_neighbor_imm_assert (input logic valid, ready);
    always_comb begin
        if (valid)
            assert (ready);
    end
endmodule
