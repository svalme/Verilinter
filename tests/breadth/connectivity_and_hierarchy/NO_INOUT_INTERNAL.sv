// Breadth test suite for NO_INOUT_INTERNAL
// Category: connectivity_and_hierarchy
//
// Tests detection of non-ANSI module-body inout port declarations, contrasting
// with ANSI header inout port declarations, non-ANSI input/output declarations,
// internal nets/tri-state drivers, and standard wire declarations.

// breadth: reports | Non-ANSI module body scalar inout declaration is reported.
// pair: p1
module internal_inout_scalar (bus);
  inout bus;
  wire bus;
endmodule

// breadth: clean | ANSI port list scalar inout header declaration is not reported.
// pair: p1
module ansi_header_inout_scalar (
    inout wire bus
);
  // ANSI port declaration in header is permitted
endmodule

// breadth: reports | Non-ANSI module body packed vector inout declaration is reported.
// pair: p2
module internal_inout_vector (bus);
  inout [7:0] bus;
  wire [7:0] bus;
endmodule

// breadth: clean | Non-ANSI module body input port declaration is not reported.
// pair: p2
module internal_input_vector (data_in);
  input [7:0] data_in;
  wire [7:0] data_in;
endmodule

// breadth: reports | Non-ANSI module body inout wire combined declaration is reported.
// pair: p3
module internal_inout_combined_wire (bus);
  inout wire [15:0] bus;
endmodule

// breadth: clean | Non-ANSI module body output wire combined declaration is not reported.
// pair: p3
module internal_output_combined_wire (data_out);
  output wire [15:0] data_out;
endmodule

// breadth: reports | Multiple non-ANSI module body inout declarations are reported.
// expect: 2
// pair: p4
module multiple_internal_inouts (bus_a, bus_b);
  inout wire [3:0] bus_a;
  inout wire [3:0] bus_b;
endmodule

// breadth: clean | Purely internal net declarations without inout keyword are not reported.
// pair: p4
module pure_internal_wires;
  wire [3:0] local_wire_a;
  wire [3:0] local_wire_b;
endmodule

// breadth: clean | ANSI inout port driven by tri-state multiplexer is not reported.
module ansi_inout_with_tristate (
    inout  wire [7:0] data_bus,
    input  wire       oe,
    input  wire [7:0] drive_data
);
  assign data_bus = oe ? drive_data : 8'bz;
endmodule

// breadth: clean | ANSI inout port connected to internal wire is not reported.
module ansi_inout_submodule_connection (
    inout wire [7:0] ext_bus
);
  wire [7:0] internal_net;
  assign internal_net = ext_bus;
endmodule
