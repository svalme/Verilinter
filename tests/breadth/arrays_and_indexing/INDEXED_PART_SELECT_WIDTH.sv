// Breadth test suite for INDEXED_PART_SELECT_WIDTH
// Category: arrays_and_indexing
//
// Tests positive constant width requirements on indexed part-selects (+: / -:),
// contrasting illegal dynamic/zero/negative widths with legal constants/parameters.

// breadth: reports
// pair: p1
module zero_width_ascending (
    input  wire [15:0] in_val,
    output wire [3:0]  out_val
);
  assign out_val = in_val[0 +: 0];
endmodule

// breadth: clean
// pair: p1
module positive_constant_width_ascending (
    input  wire [15:0] in_val,
    output wire [3:0]  out_val
);
  assign out_val = in_val[0 +: 4];
endmodule

// breadth: reports
// pair: p2
module zero_width_descending (
    input  wire [15:0] in_val,
    output wire [3:0]  out_val
);
  assign out_val = in_val[7 -: 0];
endmodule

// breadth: clean
// pair: p2
module positive_constant_width_descending (
    input  wire [15:0] in_val,
    output wire [3:0]  out_val
);
  assign out_val = in_val[7 -: 4];
endmodule

// breadth: reports
// pair: p3
module negative_width_ascending (
    input  wire [15:0] in_val,
    output wire [3:0]  out_val
);
  assign out_val = in_val[0 +: -4];
endmodule

// breadth: clean
// pair: p3
module localparam_width_ascending (
    input  wire [15:0] in_val,
    output wire [3:0]  out_val
);
  localparam int WIDTH = 4;
  assign out_val = in_val[0 +: WIDTH];
endmodule

// breadth: reports
// pair: p4
module negative_width_descending (
    input  wire [15:0] in_val,
    output wire [3:0]  out_val
);
  assign out_val = in_val[7 -: -1];
endmodule

// breadth: clean
// pair: p4
module parameter_width_descending #(
    parameter int WIDTH = 4
) (
    input  wire [15:0] in_val,
    output wire [3:0]  out_val
);
  assign out_val = in_val[7 -: WIDTH];
endmodule

// breadth: reports
// pair: p5
module dynamic_variable_width_ascending (
    input  wire [15:0] in_val,
    input  wire [3:0]  dyn_w,
    output wire [3:0]  out_val
);
  assign out_val = in_val[0 +: dyn_w];
endmodule

// breadth: clean
// pair: p5
module folded_constant_expr_width (
    input  wire [15:0] in_val,
    output wire [7:0]  out_val
);
  localparam int BASE_W = 2;
  assign out_val = in_val[0 +: (BASE_W * 4)];
endmodule

// breadth: reports
// pair: p6
module dynamic_variable_width_descending (
    input  wire [15:0] in_val,
    input  wire [3:0]  dyn_w,
    output wire [3:0]  out_val
);
  assign out_val = in_val[7 -: dyn_w];
endmodule

// breadth: clean
// pair: p6
module dynamic_base_constant_width (
    input  wire [15:0] in_val,
    input  wire [3:0]  dyn_idx,
    output wire [3:0]  out_val
);
  assign out_val = in_val[dyn_idx +: 4];
endmodule

// breadth: reports
module zero_folded_expr_width (
    input  wire [15:0] in_val,
    output wire [3:0]  out_val
);
  assign out_val = in_val[0 +: (4 - 4)];
endmodule

// breadth: clean
module width_wider_than_vector (
    input  wire [15:0] in_val,
    output wire [31:0] out_val
);
  assign out_val = in_val[0 +: 32];
endmodule
