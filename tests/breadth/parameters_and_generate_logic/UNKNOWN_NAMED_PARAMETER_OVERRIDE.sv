// Breadth test suite for UNKNOWN_NAMED_PARAMETER_OVERRIDE
// Category: parameters_and_generate_logic
//
// Tests detection of named parameter overrides targeting parameters not declared
// on the target child module, contrasting with declared value parameters,
// type parameters, undefined child modules, and localparam overrides.

// breadth: reports | Overriding non-existent parameter DEPTH on child module declaring only WIDTH is reported.
// pair: p1
module child_with_width_p1 #(
    parameter int WIDTH = 8
);
endmodule

module override_nonexistent_param;
  child_with_width_p1 #(
      .DEPTH(16) // Child declares WIDTH, not DEPTH
  ) u_child ();
endmodule

// breadth: clean | Overriding declared parameter WIDTH on child module is not reported.
// pair: p1
module child_with_width_c1 #(
    parameter int WIDTH = 8
);
endmodule

module override_valid_param;
  child_with_width_c1 #(
      .WIDTH(16)
  ) u_child ();
endmodule

// breadth: reports | Overriding parameter with misspelled name WIDHT on child module is reported.
// pair: p2
module child_with_width_p2 #(
    parameter int WIDTH = 8
);
endmodule

module override_misspelled_param;
  child_with_width_p2 #(
      .WIDHT(16) // Typo in parameter name
  ) u_child ();
endmodule

// breadth: clean | Overriding correctly spelled parameter WIDTH is not reported.
// pair: p2
module child_with_width_c2 #(
    parameter int WIDTH = 8
);
endmodule

module override_correct_spelling;
  child_with_width_c2 #(
      .WIDTH(32)
  ) u_child ();
endmodule

// breadth: reports | Overriding sibling module parameter CLK_HZ on module with only WIDTH is reported.
// pair: p3
module target_child_p3 #(
    parameter int WIDTH = 8
);
endmodule

module sibling_module_with_clk_p3 #(
    parameter int CLK_HZ = 50_000_000
);
endmodule

module override_sibling_param_name;
  // Overrides CLK_HZ on target_child_p3 which only has WIDTH
  target_child_p3 #(
      .CLK_HZ(100_000_000)
  ) u_child ();
endmodule

// breadth: clean | Overriding declared type parameter DATA_T on child module is not reported.
// pair: p3
module child_with_type_param_c3 #(
    parameter type DATA_T = int
);
endmodule

module override_type_parameter_clean;
  // Overriding a `parameter type` by name is legal and recognized
  child_with_type_param_c3 #(
      .DATA_T(logic [7:0])
  ) u_child ();
endmodule

// breadth: reports | Overriding multiple unknown parameter names on child module is reported.
// pair: p4
module child_with_width_p4 #(
    parameter int WIDTH = 8
);
endmodule

module override_multiple_unknown_params;
  child_with_width_p4 #(
      .UNKNOWN_A(1),
      .UNKNOWN_B(2)
  ) u_child ();
endmodule

// breadth: clean | Parameter override on undefined child module is not reported by this rule.
// pair: p4
module override_undefined_child_clean;
  // When child module is not defined in source, handled by UNDEFINED_MODULE
  missing_child_module #(
      .PARAM_X(1)
  ) u_child ();
endmodule

// breadth: gap | Overriding localparam is illegal in SV but not reported because resolver records it as SymbolKind.PARAMETER.
// expect: 1
module child_with_localparam_gap;
  localparam int LP_CONST = 42;
endmodule

module override_localparam_attempt;
  // Attempting to override a non-overridable localparam is invalid in IEEE 1800,
  // but currently treated as SymbolKind.PARAMETER in module symbol table.
  child_with_localparam_gap #(
      .LP_CONST(99)
  ) u_child ();
endmodule

// breadth: clean | Instantiating child module without parameter overrides is not reported.
module child_with_width_c5 #(
    parameter int WIDTH = 8
);
endmodule

module no_overrides_clean;
  child_with_width_c5 u_child ();
endmodule
