// Breadth test suite for XZ_EQUALITY_COMPARISON
// Category: operators_and_expressions
//
// Tests plain == and != equality comparisons against explicit X/Z literals,
// contrasting with === / !== (case equality), ==? / !=? (wildcard equality),
// inside sets, and comparisons against valid numeric values.

// breadth: reports
// pair: p1
module equality_x_literal_rhs (
    input  wire a,
    output wire y
);
  assign y = (a == 1'bx);
endmodule

// breadth: clean
// pair: p1
module case_equality_x_literal_rhs (
    input  wire a,
    output wire y
);
  assign y = (a === 1'bx);
endmodule

// breadth: reports
// pair: p2
module inequality_z_literal_rhs (
    input  wire a,
    output wire y
);
  assign y = (a != 1'bz);
endmodule

// breadth: clean
// pair: p2
module case_inequality_z_literal_rhs (
    input  wire a,
    output wire y
);
  assign y = (a !== 1'bz);
endmodule

// breadth: reports
// pair: p3
module equality_x_literal_lhs (
    input  wire a,
    output wire y
);
  assign y = (1'bx == a);
endmodule

// breadth: clean
// pair: p3
module case_equality_x_literal_lhs (
    input  wire a,
    output wire y
);
  assign y = (1'bx === a);
endmodule

// breadth: reports
// pair: p4
module procedural_if_xz_equality (
    input  wire [3:0] a,
    output logic      y
);
  always_comb begin
    if (a == 4'b10xz) begin
      y = 1'b1;
    end else begin
      y = 1'b0;
    end
  end
endmodule

// breadth: clean
// pair: p4
module procedural_if_wildcard_equality (
    input  wire [3:0] a,
    output logic      y
);
  always_comb begin
    if (a ==? 4'b10xz) begin
      y = 1'b1;
    end else begin
      y = 1'b0;
    end
  end
endmodule

// breadth: reports
// pair: p5
module inequality_hex_x_literal (
    input  wire [7:0] a,
    output wire       y
);
  assign y = (a != 8'hxx);
endmodule

// breadth: clean
// pair: p5
module inequality_hex_numeric_literal (
    input  wire [7:0] a,
    output wire       y
);
  assign y = (a != 8'h00);
endmodule

// breadth: clean
module inside_operator_with_x (
    input  wire       a,
    output wire       y
);
  assign y = a inside {1'bx, 1'b0};
endmodule

// breadth: clean
module casez_wildcard_item (
    input  wire [3:0] a,
    output logic      y
);
  always_comb begin
    casez (a)
      4'b1???: y = 1'b1;
      default: y = 1'b0;
    endcase
  end
endmodule

// breadth: clean
module assign_x_literal_no_comparison (
    input  wire [7:0] a,
    output wire [7:0] y
);
  assign y = a & 8'hxx;
endmodule

// breadth: clean
module wildcard_inequality_z_literal (
    input  wire a,
    output wire y
);
  assign y = (a !=? 1'bz);
endmodule
