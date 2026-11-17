// Breadth test suite for NO_QUEUE
// Category: arrays_and_indexing
//
// Tests detection of queue declarations (arr[$], arr[$:bound]),
// contrasting with fixed-size arrays and dynamic arrays.

// breadth: reports | Unbounded queue declaration arr[$] is reported.
// pair: queue_vs_fixed_array
module m;
  int q [$];
endmodule

// breadth: clean | Fixed-size array is not reported.
// pair: queue_vs_fixed_array
module m;
  int q [16];
endmodule

// breadth: clean | Queue syntax inside comments is not reported.
module m;
  // arr[$]
  logic [31:0] val;
endmodule

// breadth: reports | Bounded queue declaration arr[$:10] is reported.
module m;
  int b_q [$:10];
endmodule

// breadth: reports | Multiple queue declarations trigger multiple reports.
// expect: 2
module m;
  int q1 [$];
  int q2 [$];
endmodule

// breadth: clean | Dynamic array declaration is not reported by NO_QUEUE.
module m;
  int d_arr [];
endmodule

// breadth: clean | Dynamic array and fixed unpacked array instead of queue
module b_clean_neighbor_arrays (input logic clk);
    int dyn_arr [];
    int fixed_arr [4];
endmodule
