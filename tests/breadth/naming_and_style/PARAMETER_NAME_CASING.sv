// Breadth tests for PARAMETER_NAME_CASING
// Rule: Flags parameter and localparam declarations whose names are not ALL_CAPS_WITH_UNDERSCORES.

// breadth: reports | Lowercase module port-list parameter is reported.
// pair: module_parameter
module module_parameter_lower #(parameter width = 8);
endmodule

// breadth: clean | ALL_CAPS module port-list parameter is not reported.
// pair: module_parameter
module module_parameter_upper #(parameter WIDTH = 8);
endmodule

// breadth: reports | CamelCase localparam declaration in module body is reported.
// pair: localparam_casing
module localparam_camel_case;
  localparam maxCount = 16;
endmodule

// breadth: clean | ALL_CAPS localparam declaration in module body is not reported.
// pair: localparam_casing
module localparam_all_caps;
  localparam MAX_COUNT = 16;
endmodule

// breadth: reports | Lowercase body parameter declaration is reported.
// pair: body_parameter
module body_parameter_lower;
  parameter latency = 2;
endmodule

// breadth: clean | ALL_CAPS body parameter declaration is not reported.
// pair: body_parameter
module body_parameter_upper;
  parameter LATENCY = 2;
endmodule

// breadth: reports | Lowercase package-level parameter declaration is reported.
// pair: package_parameter
package package_parameter_lower;
  parameter baud_rate = 9600;
endpackage

// breadth: clean | ALL_CAPS package-level parameter declaration is not reported.
// pair: package_parameter
package package_parameter_upper;
  parameter BAUD_RATE = 9600;
endpackage

// breadth: clean | Lowercase net declaration is not reported because it is not a parameter.
module ordinary_wire_lower;
  wire lower_wire;
endmodule

// breadth: clean | Enum member declarations are not reported because they are not parameters.
module enum_member_not_flagged;
  typedef enum { idle, active } state_t;
endmodule
