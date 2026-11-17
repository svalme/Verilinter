// Breadth test suite for NO_STRING_TYPE
// Category: declarations_and_types
//
// Tests detection of simulation-only string data type declarations,
// contrasting with fixed-size byte arrays, packed vectors, and comments.

// breadth: reports | Declaration of string variable is reported.
// pair: string_vs_byte_array
module m;
  string s;
endmodule

// breadth: clean | Fixed-size unpacked byte array is not reported.
// pair: string_vs_byte_array
module m;
  byte s [16];
endmodule

// breadth: clean | Word string inside comments is not reported.
module m;
  // Note about string type
  reg [63:0] label_reg;
  initial label_reg = 64'h0;
endmodule

// breadth: reports | String variable declared in package scope is reported.
package p;
  string banner;
endpackage

// breadth: reports | Multiple string variable declarations trigger multiple reports.
// expect: 2
module m;
  string first_name;
  string last_name;
endmodule

// breadth: clean | Standard wire and logic declarations are not reported.
module m;
  wire [7:0] raw_byte;
  logic valid;
endmodule

// breadth: clean | Int, logic, event, and chandle variables instead of string type
module b_clean_neighbor_types (input logic clk);
    int code;
    logic [7:0] bus;
    event sync_ev;
    chandle ptr;
endmodule
