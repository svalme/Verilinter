// Breadth test suite for NO_ASSOCIATIVE_ARRAY
// Category: arrays_and_indexing
//
// Tests detection of associative array declarations (arr[string], arr[*], arr[int]),
// contrasting with fixed-size unpacked arrays and multidimensional arrays.

// breadth: reports | Associative array indexed by string is reported.
// pair: assoc_vs_fixed_array
module m;
  int tbl [string];
endmodule

// breadth: clean | Fixed-size unpacked array is not reported.
// pair: assoc_vs_fixed_array
module m;
  int tbl [16];
endmodule

// breadth: clean | Associative array index syntax inside comments is not reported.
module m;
  // arr[string] arr[*]
  logic [7:0] mem [0:255];
endmodule

// breadth: reports | Wildcard associative array index [*] is reported.
module m;
  int lut [*];
endmodule

// breadth: reports | Multiple associative array declarations trigger multiple reports.
// expect: 2
module m;
  int map1 [int];
  int map2 [string];
endmodule

// breadth: clean | Multidimensional fixed-size array is not reported.
module m;
  logic [7:0] matrix [0:3][0:3];
endmodule
