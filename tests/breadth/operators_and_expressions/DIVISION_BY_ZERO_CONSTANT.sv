// Breadth test suite for DIVISION_BY_ZERO_CONSTANT
// Category: operators_and_expressions
//
// Tests division or modulo by constant zero divisors, legal non-zero divisors,
// and runtime variable divisors.

// breadth: reports
// pair: p1
module div_by_zero_unsized (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = x / 0;
endmodule

// breadth: clean
// pair: p1
module div_by_one_unsized (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = x / 1;
endmodule

// breadth: reports
// pair: p2
module mod_by_zero_unsized (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = x % 0;
endmodule

// breadth: clean
// pair: p2
module mod_by_nonzero_unsized (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = x % 8;
endmodule

// breadth: reports
// pair: p3
module div_by_sized_zero (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = x / 4'd0;
endmodule

// breadth: clean
// pair: p3
module div_by_sized_nonzero (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = x / 4'd4;
endmodule

// breadth: reports
// pair: p4
module div_by_hex_zero_procedural (
    input  wire [7:0] x,
    output logic [7:0] y
);
  always_comb begin
    y = x / 8'h00;
  end
endmodule

// breadth: clean
// pair: p4
module div_by_hex_nonzero_procedural (
    input  wire [7:0] x,
    output logic [7:0] y
);
  always_comb begin
    y = x / 8'h10;
  end
endmodule

// breadth: reports
// pair: p5
module mod_by_binary_zero (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = x % 2'b00;
endmodule

// breadth: clean
// pair: p5
module mod_by_binary_nonzero (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = x % 2'b10;
endmodule

// breadth: reports
// pair: p6
module div_by_1bit_zero (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = x / 1'b0;
endmodule

// breadth: clean
// pair: p6
module div_zero_numerator (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = 8'd0 / x;
endmodule

// breadth: clean
module div_by_runtime_variable (
    input  wire [7:0] x,
    input  wire [7:0] n,
    output wire [7:0] y
);
  assign y = x / n;
endmodule

// breadth: clean
module multiply_by_zero (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = x * 0;
endmodule

// breadth: gap | A divisor that is a localparam with the value 0 is a constant zero, but the rule reports only a literal zero.
// expect: 1
module div_by_param_zero (
    input  wire [7:0] x,
    output wire [7:0] y
);
  localparam int ZERO = 0;
  assign y = x / ZERO;
endmodule

// breadth: gap | A real literal divisor equal to 0.0 is a constant zero, but the rule reports only an integer zero.
// expect: 1
module div_by_real_zero (
    input  wire [7:0] x,
    output wire [7:0] y
);
  assign y = x / 0.0;
endmodule
