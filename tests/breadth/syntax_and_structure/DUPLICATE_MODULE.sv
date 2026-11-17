// Breadth test suite for DUPLICATE_MODULE
// Category: syntax_and_structure
//
// Tests detection of duplicate module/interface definitions sharing the same identifier,
// contrasting with uniquely named modules, packages sharing names with modules,
// and distinct modules within the same compilation unit.

// breadth: reports | Two module declarations sharing the same identifier dup_mod_p1 are reported.
// pair: p1
module dup_mod_p1;
  wire a;
endmodule

module dup_mod_p1;
  wire b;
endmodule

// breadth: clean | Uniquely named module declaration unique_mod_c1 is not reported.
// pair: p1
module unique_mod_c1;
  wire a;
endmodule

// breadth: reports | Interface and module declarations sharing the same identifier shared_name_p2 are reported.
// pair: p2
interface shared_name_p2;
  logic clk;
endinterface

module shared_name_p2;
  wire d;
endmodule

// breadth: clean | Distinctly named interface distinct_if_c2 and module distinct_mod_c2 are not reported.
// pair: p2
interface distinct_if_c2;
  logic clk;
endinterface

module distinct_mod_c2;
  wire d;
endmodule

// breadth: reports | Three module declarations sharing the same identifier tri_dup_p3 are reported.
// expect: 2
// pair: p3
module tri_dup_p3;
  wire a;
endmodule

module tri_dup_p3;
  wire b;
endmodule

module tri_dup_p3;
  wire c;
endmodule

// breadth: clean | Two distinctly named modules within the same file are not reported.
// pair: p3
module multi_distinct_a_c3;
  wire a;
endmodule

module multi_distinct_b_c3;
  wire b;
endmodule

// breadth: clean | Package declaration sharing a name with a module is not a duplicate module and is not reported.
// pair: p4
package pkg_shared_p4;
  parameter int X = 1;
endpackage

module pkg_shared_p4;
  // Package sharing a name with a module is not a duplicate module definition
  logic clk;
endmodule

// breadth: reports | Two parameterized module declarations sharing the same identifier are reported.
// pair: p4
module parameterized_dup_p4 #(
    parameter int W = 8
);
  wire [W-1:0] data;
endmodule

module parameterized_dup_p4 #(
    parameter int W = 16
);
  wire [W-1:0] data;
endmodule

// breadth: clean | Hierarchical parent and child modules with distinct names are not reported.
module hierarchy_distinct_parent_c5;
  hierarchy_distinct_child_c5 u_child ();
endmodule

module hierarchy_distinct_child_c5;
endmodule

// breadth: clean | Standalone interface declaration with unique name is not reported.
interface standalone_interface_c6;
  logic rst_n;
endinterface
