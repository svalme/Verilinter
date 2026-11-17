// Breadth test suite for REVERSED_INDEXED_PART_SELECT
// Category: arrays_and_indexing
//
// Tests detection of reversed indexed part-select operator typos (':+' or ':-')
// instead of '+:' or '-:', contrasting with valid indexed part-selects,
// valid simple slices, spaced unary operators, reversed slice directions,
// and memory word slices.

// breadth: reports
// pair: p1
module reversed_colon_plus_space (
    input  wire [7:0] r,
    output wire [1:0] z
);
  assign z = r[2 :+ 1];
endmodule

// breadth: clean
// pair: p1
module valid_ascending_indexed_part_select (
    input  wire [7:0] r,
    output wire [1:0] z
);
  assign z = r[2 +: 1];
endmodule

// breadth: reports
// pair: p2
module reversed_colon_plus_tight (
    input  wire [7:0] r,
    output wire [1:0] z
);
  assign z = r[2 :+1];
endmodule

// breadth: clean
// pair: p2
module spaced_unary_plus_slice (
    input  wire [7:0] r,
    output wire [1:0] z
);
  assign z = r[2 : +1];
endmodule

// breadth: reports
// pair: p3
module reversed_colon_minus_space (
    input  wire [7:0] r,
    output wire [1:0] z
);
  assign z = r[2 :- 1];
endmodule

// breadth: clean
// pair: p3
module valid_descending_indexed_part_select (
    input  wire [7:0] r,
    output wire [1:0] z
);
  assign z = r[2 -: 1];
endmodule

// breadth: reports
// pair: p4
module reversed_colon_minus_tight (
    input  wire [7:0] r,
    output wire [1:0] z
);
  assign z = r[2 :-1];
endmodule

// breadth: clean
// pair: p4
module spaced_unary_minus_slice (
    input  wire [7:0] r,
    output wire [1:0] z
);
  assign z = r[2 : -1];
endmodule

// breadth: reports
// pair: p5
module procedural_reversed_colon_plus (
    input  wire [7:0] r,
    output logic [1:0] z
);
  always_comb begin
    z = r[3 :+ 2];
  end
endmodule

// breadth: clean
// pair: p5
module procedural_valid_indexed_part_select (
    input  wire [7:0] r,
    output logic [1:0] z
);
  always_comb begin
    z = r[3 +: 2];
  end
endmodule

// breadth: clean
module reversed_vector_slice (
    input  wire [0:7] in_vec,
    output wire [3:0] out_vec
);
  assign out_vec = in_vec[3:0];
endmodule

// breadth: clean
module normal_vector_slice (
    input  wire [7:0] in_vec,
    output wire [3:0] out_vec
);
  assign out_vec = in_vec[7:4];
endmodule

// breadth: clean
module memory_word_slice (
    input  wire [1:0] addr,
    output wire [3:0] out_vec
);
  reg [7:0] mem [0:3];
  assign out_vec = mem[addr][3:0];
endmodule

// breadth: clean
module parameter_range_slice #(
    parameter int HI = 3,
    parameter int LO = 0
) (
    input  wire [7:0] in_vec,
    output wire [3:0] out_vec
);
  assign out_vec = in_vec[HI:LO];
endmodule
