// Breadth tests for MODULE_NAME_CASING
// Rule: Flags module declarations whose names are not lower_snake_case.

// breadth: reports | CamelCase module identifier is reported.
// pair: camel_vs_snake
module myModule;
endmodule

// breadth: clean | Lower snake_case module identifier is not reported.
// pair: camel_vs_snake
module my_module;
endmodule

// breadth: reports | UPPER_CASE module identifier is reported.
// pair: caps_vs_lower
module ALU_BLOCK;
endmodule

// breadth: clean | Lowercase module identifier alu_block is not reported.
// pair: caps_vs_lower
module alu_block;
endmodule

// breadth: reports | PascalCase module identifier ControllerUnit is reported.
// pair: pascal_vs_lower
module ControllerUnit;
endmodule

// breadth: clean | Lowercase module identifier with trailing version digits is not reported.
// pair: pascal_vs_lower
module controller_unit_v2;
endmodule

// breadth: reports | Module name starting with leading underscore is reported.
// pair: underscore_prefix
module _hidden_submodule;
endmodule

// breadth: clean | Module name with trailing underscore starting with lowercase letter is not reported.
// pair: underscore_prefix
module hidden_submodule_;
endmodule

// breadth: clean | Single-letter lowercase module identifier is not reported.
module m;
endmodule

// breadth: clean | Lowercase module identifier starting with letter followed by digits and underscore is not reported.
module u123_456;
endmodule
