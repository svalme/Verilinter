// Breadth test suite for NO_COVERGROUP_DECLARATION
// Category: assertions_and_verification
//
// Tests detection of functional coverage covergroup declarations,
// contrasting with status registers and comments.

// breadth: reports | Covergroup declaration inside module is reported.
// pair: covergroup_vs_reg
module m;
  covergroup cg;
  endgroup
endmodule

// breadth: clean | Standard status register is not reported.
// pair: covergroup_vs_reg
module m;
  reg [31:0] coverage_count;
endmodule

// breadth: clean | Word covergroup inside comments is not reported.
module m;
  // covergroup
  wire w = 1'b0;
endmodule

// breadth: reports | Covergroup declaration with sample argument is reported.
module m;
  covergroup cg_arg (int val);
  endgroup
endmodule

// breadth: reports | Multiple covergroup declarations trigger multiple reports.
// expect: 2
module m;
  covergroup cg1;
  endgroup
  covergroup cg2;
  endgroup
endmodule

// breadth: clean | Standard class declaration without covergroups is not reported.
module m;
  class worker;
    int id;
  endclass
endmodule

// breadth: clean | Plain typedef struct instead of covergroup declaration
module b_clean_neighbor_struct (input logic clk);
    typedef struct {
        int sample_id;
        logic [7:0] val;
    } sample_t;
    sample_t s;
endmodule
