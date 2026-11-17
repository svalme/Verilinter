// Breadth test suite for NO_CHANDLE_TYPE
// Category: declarations_and_types
//
// Tests detection of DPI-only chandle handle type declarations,
// contrasting with integral and bit vector storage.

// breadth: reports | Declaration of chandle handle variable is reported.
// pair: chandle_vs_int
module m;
  chandle handle_ptr;
endmodule

// breadth: clean | Unsigned longint representation is not reported.
// pair: chandle_vs_int
module m;
  longint unsigned handle_ptr;
endmodule

// breadth: clean | Word chandle inside comments is not reported.
module m;
  // chandle
  logic [31:0] ptr_val;
endmodule

// breadth: reports | Chandle variable declared inside a package is reported.
package p;
  chandle ctx_handle;
endpackage

// breadth: reports | Multiple chandle variable declarations trigger multiple reports.
// expect: 2
module m;
  chandle h1;
  chandle h2;
endmodule

// breadth: clean | Integral and bit vector declarations are not reported.
module m;
  int unsigned h_id;
  bit [63:0] opaque_addr;
endmodule

// breadth: clean | Supported data types including int and string instead of chandle
module b_clean_neighbor_types (input logic clk);
    int cnt;
    longint big_cnt;
    string name;
    event ev;
endmodule
