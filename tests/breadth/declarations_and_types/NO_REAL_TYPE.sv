// Breadth test suite for NO_REAL_TYPE
// Category: declarations_and_types
//
// Tests detection of real, shortreal, and realtime floating-point data types,
// contrasting with integral and fixed-point data types.

// breadth: reports | Declaration of real floating-point variable is reported.
// pair: real_vs_logic
module m;
  real r_val;
endmodule

// breadth: clean | Fixed-point logic vector is not reported.
// pair: real_vs_logic
module m;
  logic [31:0] fixed_val;
endmodule

// breadth: clean | Keyword real inside comments or string literals is not reported.
module m;
  /* real shortreal realtime */
  wire [31:0] w;
endmodule

// breadth: reports | Shortreal type declaration in package scope is reported.
package p;
  shortreal sr_val;
endpackage

// breadth: reports | Realtime variable and real type in function trigger multiple reports.
// expect: 2
module m;
  realtime rt_val;
  function void calculate();
    real tmp;
  endfunction
endmodule

// breadth: clean | Integral integer and time declarations are not reported.
module m;
  integer int_val;
  time t_val;
endmodule

// breadth: clean | Integer, string, and event types instead of real type
module b_clean_neighbor_types (input logic clk);
    int count;
    integer step;
    string label_str;
    event tick_ev;
endmodule
