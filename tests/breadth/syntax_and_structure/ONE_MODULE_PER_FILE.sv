// Breadth test suite for ONE_MODULE_PER_FILE
// Category: syntax_and_structure
//
// Tests detection of files containing multiple module declarations, contrasting
// with files containing a single module, a module alongside a package or interface,
// and files without module declarations.

// breadth: reports | Second module declared in the same file is reported.
// pair: p1
module first_module;
  wire a;
endmodule

module second_module; // Second module declared in the same file
  wire b;
endmodule

// breadth: clean | Single module declaration in file is not reported.
// pair: p1
module sole_module_in_file;
  wire a;
endmodule

// breadth: reports | Three modules in one file trigger reports on second and third declarations.
// expect: 2
// pair: p2
module mod_one;
  wire a;
endmodule

module mod_two;
  wire b;
endmodule

module mod_three;
  wire c;
endmodule

// breadth: clean | Module declared alongside a package in the same file is not reported.
// pair: p2
package helper_package;
  parameter int TIMEOUT = 100;
endpackage

module module_with_package;
  wire sig;
endmodule

// breadth: reports | Parent and child modules defined together in the same file are reported.
// pair: p3
module parent_module;
  child_module u_child ();
endmodule

module child_module;
  wire child_wire;
endmodule

// breadth: clean | Module declared alongside an interface in the same file is not reported.
// pair: p3
interface bus_interface;
  logic clk;
  logic rst_n;
endinterface

module module_with_interface;
  wire sig;
endmodule

// breadth: clean | Single module declared alongside both a package and an interface is not reported.
// pair: p4
package constants_pkg;
  parameter int WIDTH = 8;
endpackage

interface control_if;
  logic valid;
endinterface

module single_module_multi_units;
  wire [7:0] data;
endmodule

// breadth: reports | Two parameterized modules declared in the same file are reported.
// pair: p4
module param_module_a #(
    parameter int W = 8
);
  wire [W-1:0] a;
endmodule

module param_module_b #(
    parameter int W = 8
);
  wire [W-1:0] b;
endmodule

// breadth: clean | File containing only an interface without modules is not reported.
interface standalone_interface_file;
  logic [3:0] addr;
endinterface

// breadth: clean | File containing only a package without modules is not reported.
package standalone_package_file;
  parameter int VERSION = 1;
endpackage
