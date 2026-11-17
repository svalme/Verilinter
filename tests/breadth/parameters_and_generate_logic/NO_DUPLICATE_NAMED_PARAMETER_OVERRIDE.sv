// Breadth test suite for NO_DUPLICATE_NAMED_PARAMETER_OVERRIDE
// Category: parameters_and_generate_logic
//
// Tests detection of duplicate named parameter overrides within the same
// module instantiation, contrasting with distinct parameter overrides,
// cross-instance reuses, ordered overrides, and type parameter overrides.

// breadth: reports | Duplicate override of named parameter WIDTH in the same instance is reported.
// pair: p1
module child_params #(
    parameter int WIDTH = 8,
    parameter int DEPTH = 16
);
endmodule

module duplicate_named_param_values;
  child_params #(
      .WIDTH(8),
      .WIDTH(16) // Duplicate override of parameter WIDTH
  ) u_child ();
endmodule

// breadth: clean | Distinct named parameter overrides WIDTH and DEPTH are not reported.
// pair: p1
module distinct_named_params;
  child_params #(
      .WIDTH(8),
      .DEPTH(16)
  ) u_child ();
endmodule

// breadth: reports | Repeated override of parameter P with identical value in same instance is reported.
// pair: p2
module child_single_param #(
    parameter int P = 0
);
endmodule

module duplicate_param_same_value;
  child_single_param #(
      .P(1),
      .P(1)
  ) u_child ();
endmodule

// breadth: clean | Single named parameter override is not reported.
// pair: p2
module single_named_param_clean;
  child_single_param #(
      .P(1)
  ) u_child ();
endmodule

// breadth: reports | Duplicate override of parameter A among three parameter overrides is reported.
// pair: p3
module child_three_params #(
    parameter int A = 1,
    parameter int B = 2,
    parameter int C = 3
);
endmodule

module three_params_with_duplicate;
  child_three_params #(
      .A(10),
      .B(20),
      .A(30)
  ) u_child ();
endmodule

// breadth: clean | Parameter P overridden across two distinct instances independently is not reported.
// pair: p3
module same_param_across_two_instances;
  // Overriding parameter P across separate instances is valid and standard
  child_single_param #(.P(1)) u_inst1 ();
  child_single_param #(.P(2)) u_inst2 ();
endmodule

// breadth: clean | Ordered positional parameter overrides without named keys are not reported.
// pair: p4
module ordered_parameter_overrides;
  // Ordered overrides do not specify parameter names
  child_params #(8, 32) u_child ();
endmodule

// breadth: reports | Duplicate override of type parameter T in the same instance is reported.
// pair: p4
module child_type_param #(
    parameter type T = int
);
endmodule

module duplicate_type_param_override;
  child_type_param #(
      .T(int),
      .T(logic [7:0])
  ) u_child ();
endmodule

// breadth: clean | Explicit empty parameter override list is not reported.
module empty_parameter_override_clean;
  child_single_param #() u_child ();
endmodule

// breadth: clean | Module instantiation using default parameter values without override is not reported.
module default_parameters_no_override;
  child_params u_child ();
endmodule
