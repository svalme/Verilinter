// case: reports | A plain signal narrower than its target is extended, which the rule reports.
// pair: plain-versus-left-shift
module top(input wire [3:0] a, output wire [7:0] o);
  assign o = a;
endmodule

// case: clean | A left shift into a wider target is sized on purpose to hold the result.
// pair: plain-versus-left-shift
module top(input wire [3:0] a, output wire [7:0] o);
  assign o = a << 2;
endmodule

// case: reports | A left shift whose operand is wider than the target loses bits.
module top(input wire [7:0] r, output wire [3:0] o);
  assign o = r << 1;
endmodule

// case: clean | A wide slice shifted left into a 32-bit target.
module top(input wire [31:0] r, output wire [31:0] o);
  assign o = r[31:12] << 12;
endmodule

// case: reports | A conditional expression narrower than the target is the same extension a plain signal gets.
module top(input wire s, input wire [3:0] a, b, output wire [7:0] o);
  assign o = s ? a : b;
endmodule

// case: clean | Whole unpacked arrays assigned from arrays of the same shape.
module top(output logic [31:0] o [10], output logic [31:0] o2 [10], input logic [31:0] i [10], input logic [31:0] st [2][10]);
  assign o = i;
  assign o2 = st[1];
endmodule

// case: reports | An array element wider than its target loses bits.
module top(output wire [7:0] x, input logic [15:0] one [4]);
  assign x = one[1];
endmodule
