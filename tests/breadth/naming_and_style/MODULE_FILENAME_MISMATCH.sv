// Breadth test suite for MODULE_FILENAME_MISMATCH
// Category: naming_and_style
//
// Tests detection of files where no declared module name matches the filename stem
// (the inline breadth test harness compiles files as "top.sv", stem "top"),
// contrasting matching module names, multi-module files with at least one matching name,
// and interface/package declarations.

// breadth: reports | Single module declared with name mismatched_single_name not matching filename top is reported.
// pair: p1
module mismatched_single_name;
  wire a;
endmodule

// breadth: clean | Module declared with name top matching filename top is not reported.
// pair: p1
module top;
  wire a;
endmodule

// breadth: reports | File containing modules secondary_a and secondary_b where neither matches top is reported.
// pair: p2
module secondary_a;
  wire a;
endmodule

module secondary_b;
  wire b;
endmodule

// breadth: clean | Multi-module file containing helper_module and top where top matches filename is not reported.
// pair: p2
module helper_module;
  wire a;
endmodule

module top;
  wire b;
endmodule

// breadth: reports | Module with ports declared with non-matching name submodule_with_ports is reported.
// pair: p3
module submodule_with_ports (
    input  wire in_val,
    output wire out_val
);
  assign out_val = in_val;
endmodule

// breadth: clean | Module with ports declared with name top matching filename is not reported.
// pair: p3
module top (
    input  wire in_val,
    output wire out_val
);
  assign out_val = in_val;
endmodule

// breadth: clean | Auxiliary interface along with module top matching filename is not reported.
// pair: p4
interface aux_interface;
  logic clk;
endinterface

module top;
  wire a;
endmodule

// breadth: reports | Interface named top with module worker_module where no module matches top is reported.
// pair: p4
interface top; // Interface named top, but module is not named top
  logic clk;
endinterface

module worker_module;
  wire a;
endmodule

// breadth: clean | Parameterized module top matching filename stem is not reported.
module top #(
    parameter int WIDTH = 8
) (
    input  wire [WIDTH-1:0] in_bus,
    output wire [WIDTH-1:0] out_bus
);
  assign out_bus = in_bus;
endmodule

// breadth: clean | Module top instantiating sub_worker where top matches filename is not reported.
module sub_worker;
  wire sig;
endmodule

module top;
  sub_worker u_sub ();
endmodule
