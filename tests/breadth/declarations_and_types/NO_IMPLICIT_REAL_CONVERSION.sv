// Breadth test suite for NO_IMPLICIT_REAL_CONVERSION
// Category: declarations_and_types
//
// Tests detection of implicit real-to-integral conversions where fractional precision
// is discarded, contrasting with explicit type casts, integral-to-real conversions,
// whole-number real literals, real-to-real assignments, and comparisons.

// breadth: reports | Implicit conversion of fractional real literal to int in variable declaration is reported.
// pair: p1
module declarator_fractional_real (
    output wire [31:0] out_val
);
  int x = 3.5; // Implicit conversion of fractional real literal to int
  assign out_val = x;
endmodule

// breadth: clean | Explicit cast int'(3.5) to integral type is not reported.
// pair: p1
module declarator_explicit_cast (
    output wire [31:0] out_val
);
  int x = int'(3.5); // Explicit cast to integral type is permitted
  assign out_val = x;
endmodule

// breadth: reports | Continuous assignment of fractional real literal to integer wire is reported.
// pair: p2
module continuous_assign_fractional_real (
    output wire [7:0] y
);
  assign y = 4.2; // Continuous assignment of fractional real literal to integer wire
endmodule

// breadth: clean | Integer value assigned to real variable preserves precision and is not reported.
// pair: p2
module integer_to_real_conversion (
    output wire [63:0] r_bits
);
  real r = 5; // Integral value converted to real preserves precision
  assign r_bits = $realtobits(r);
endmodule

// breadth: reports | Procedural assignment of fractional real literal to integer register is reported.
// pair: p3
module procedural_assign_fractional_real (
    output reg [7:0] y
);
  always_comb begin
    y = 1.75; // Procedural assignment of fractional real literal
  end
endmodule

// breadth: clean | Real-to-real assignment between real variables is not reported.
// pair: p3
module real_to_real_assignment (
    input  wire [63:0] in_bits,
    output wire [63:0] out_bits
);
  real r_in, r_out;
  assign r_in = $bitstoreal(in_bits);
  always_comb begin
    r_out = r_in;
  end
  assign out_bits = $realtobits(r_out);
endmodule

// breadth: reports | Fractional time literal implicitly converted to integer variable is reported.
// pair: p4
module fractional_time_literal_to_int (
    output wire [31:0] out_val
);
  int t = 1.5ns; // Fractional time literal implicitly converted to integral int
  assign out_val = t;
endmodule

// breadth: clean | Real literal in relational comparison expression is not reported.
// pair: p4
module real_in_comparison_expression (
    input  wire [63:0] in_bits,
    output wire        cmp_result
);
  real r;
  assign r = $bitstoreal(in_bits);
  assign cmp_result = (r > 2.5); // Real in comparison expression does not convert to target
endmodule

// breadth: clean | Real literal with zero fractional part has no fractional loss and is not reported.
module whole_number_real_literal (
    output wire [31:0] out_val
);
  // Real literal with zero fractional part has no fractional precision loss
  int x = 3.0;
  assign out_val = x;
endmodule

// breadth: clean | Real literal assigned to real variable target is not reported.
module real_literal_to_real_target (
    output wire [63:0] out_bits
);
  real r = 3.14159; // Real literal assigned to real target
  assign out_bits = $realtobits(r);
endmodule
