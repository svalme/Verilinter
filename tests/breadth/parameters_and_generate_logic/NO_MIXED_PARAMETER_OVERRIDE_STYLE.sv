// Breadth test suite for NO_MIXED_PARAMETER_OVERRIDE_STYLE
// Category: parameters_and_generate_logic
//
// Tests detection of module instances mixing named and ordered parameter
// overrides within the same parameter override list, contrasting with homogeneous
// named/ordered overrides, single-parameter overrides, and empty override lists.

// breadth: reports | Parameter override mixing positional override followed by named override is reported.
// pair: p1
module child_params_two #(
    parameter int WIDTH = 8,
    parameter int DEPTH = 16
);
endmodule

module mixed_ordered_then_named;
  child_params_two #(
      8,
      .DEPTH(16) // Named override mixed with preceding ordered override
  ) u_child ();
endmodule

// breadth: clean | Parameter override using exclusively named overrides is not reported.
// pair: p1
module homogeneous_named_overrides;
  child_params_two #(
      .WIDTH(8),
      .DEPTH(16)
  ) u_child ();
endmodule

// breadth: reports | Parameter override mixing named override followed by positional override is reported.
// pair: p2
module mixed_named_then_ordered;
  child_params_two #(
      .WIDTH(8),
      16 // Ordered override mixed with preceding named override
  ) u_child ();
endmodule

// breadth: clean | Parameter override using exclusively positional overrides is not reported.
// pair: p2
module homogeneous_ordered_overrides;
  child_params_two #(
      8,
      16
  ) u_child ();
endmodule

// breadth: reports | Positional override sandwiched between two named overrides is reported.
// pair: p3
module child_params_three #(
    parameter int A = 1,
    parameter int B = 2,
    parameter int C = 3
);
endmodule

module mixed_named_ordered_named;
  child_params_three #(
      .A(10),
      20,
      .C(30)
  ) u_child ();
endmodule

// breadth: clean | Single named parameter override is not reported.
// pair: p3
module single_named_override_clean;
  child_params_two #(
      .WIDTH(8)
  ) u_child ();
endmodule

// breadth: reports | Named type parameter override mixed with positional parameter override is reported.
// pair: p4
module child_type_and_val #(
    parameter type T = int,
    parameter int  W = 4
);
endmodule

module mixed_type_and_ordered_override;
  child_type_and_val #(
      .T(logic [7:0]),
      8
  ) u_child ();
endmodule

// breadth: clean | Single positional parameter override is not reported.
// pair: p4
module single_ordered_override_clean;
  child_params_two #(
      8
  ) u_child ();
endmodule

// breadth: clean | Explicit empty parameter override is not reported.
module empty_override_clean;
  child_params_two #() u_child ();
endmodule

// breadth: clean | Module instantiation with default parameter values is not reported.
module default_parameters_clean;
  child_params_two u_child ();
endmodule
