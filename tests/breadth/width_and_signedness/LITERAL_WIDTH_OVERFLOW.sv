// breadth: reports | A sized decimal literal one above the largest value of its declared width is reported.
// pair: decimal-literal-width
module top(output logic [3:0] o);
  assign o = 4'd16;
endmodule

// breadth: clean | A sized decimal literal at the largest value of its declared width is not reported.
// pair: decimal-literal-width
module top(output logic [3:0] o);
  assign o = 4'd15;
endmodule

// breadth: reports | A sized binary literal whose value requires more bits than declared is reported.
// pair: binary-literal-width
module top(output logic [1:0] o);
  assign o = 2'b111;
endmodule

// breadth: clean | A sized binary literal whose value fits within its declared width is not reported.
// pair: binary-literal-width
module top(output logic [1:0] o);
  assign o = 2'b11;
endmodule

// breadth: reports | A sized hexadecimal literal whose value requires more bits than declared is reported.
// pair: hex-literal-width
module top(output logic [3:0] o);
  assign o = 4'hFF;
endmodule

// breadth: clean | A sized hexadecimal literal whose value fits within its declared width is not reported.
// pair: hex-literal-width
module top(output logic [7:0] o);
  assign o = 8'hFF;
endmodule

// breadth: reports | A sized octal literal whose value requires more bits than declared is reported.
// pair: octal-literal-width
module top(output logic [2:0] o);
  assign o = 3'o10;
endmodule

// breadth: clean | A sized octal literal whose value fits within its declared width is not reported.
// pair: octal-literal-width
module top(output logic [2:0] o);
  assign o = 3'o7;
endmodule

// breadth: clean | A signed sized literal that fits its declared width is not reported.
module top(output logic signed [3:0] o);
  assign o = 4'sd5;
endmodule

// breadth: clean | An unsized decimal literal is not checked by this rule.
module top(output logic [31:0] o);
  assign o = 100;
endmodule

// breadth: clean | A sized vector with x digits is not checked by this rule.
module top(output logic [3:0] o);
  assign o = 4'bxx01;
endmodule

// breadth: gap | A signed sized literal whose value needs more bits than declared is a real overflow, but the rule only checks unsigned literals.
module top(output logic signed [3:0] o);
  assign o = 4'sd20;
endmodule

// breadth: reports | An overflowing sized literal used as an operand of an expression is reported.
module top(input logic [3:0] a, output logic [3:0] o);
  assign o = a + 4'd20;
endmodule

// breadth: reports | An overflowing sized literal connected to an instance port is reported.
module child(input logic [3:0] p);
endmodule
module top(output logic o);
  child u(.p(4'd20));
  assign o = 1'b0;
endmodule

// breadth: reports | An overflowing sized literal used as a case item is reported.
module top(input logic [3:0] a, input logic [3:0] b, output logic [3:0] o);
  always_comb begin
    case (a)
      4'd20: o = b;
      default: o = 4'd0;
    endcase
  end
endmodule

// breadth: reports | An overflowing sized literal in a localparam initializer is reported.
module top(output logic [3:0] o);
  localparam [3:0] P = 4'd20;
  assign o = P;
endmodule

// breadth: reports | Underscores in the digits do not hide an overflow.
module top(output logic [7:0] o);
  assign o = 8'h1_FF;
endmodule

// breadth: reports | A negated overflowing sized literal still overflows before the negation.
module top(output logic [3:0] o);
  assign o = -4'd20;
endmodule
