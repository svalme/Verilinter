// Breadth test suite for NO_DYNAMIC_ARRAY
// Category: arrays_and_indexing
//
// Tests detection of dynamic array declarations (arr[]),
// contrasting with fixed-size arrays and queues.

// breadth: reports | Dynamic array declaration arr[] is reported.
// pair: dynamic_vs_fixed_array
module m;
  int d_arr [];
endmodule

// breadth: clean | Fixed-size array is not reported.
// pair: dynamic_vs_fixed_array
module m;
  int f_arr [16];
endmodule

// breadth: clean | Dynamic array syntax inside comments is not reported.
module m;
  // arr[]
  logic [31:0] val;
endmodule

// breadth: reports | Dynamic array declared in package scope is reported.
package p;
  byte dyn_buffer [];
endpackage

// breadth: reports | Multiple dynamic array declarations trigger multiple reports.
// expect: 2
module m;
  int arr1 [];
  int arr2 [];
endmodule

// breadth: clean | Queue declaration is not reported by NO_DYNAMIC_ARRAY.
module m;
  int q_arr [$];
endmodule
