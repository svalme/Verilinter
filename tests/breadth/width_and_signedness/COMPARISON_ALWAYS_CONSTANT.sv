// breadth: reports | An unsigned operand compared `< 0` is always false because an unsigned value is never negative.
// pair: lower-bound-lt
module top(input wire [3:0] a, output wire o);
  assign o = a < 0;
endmodule

// breadth: clean | Comparing an unsigned operand `< 1` is true for zero and false for non-zero values.
// pair: lower-bound-lt
module top(input wire [3:0] a, output wire o);
  assign o = a < 1;
endmodule

// breadth: reports | An unsigned operand compared `>= 0` is always true.
// pair: lower-bound-ge
module top(input wire [3:0] a, output wire o);
  assign o = a >= 0;
endmodule

// breadth: clean | Comparing an unsigned operand `>= 1` is false when the operand is zero.
// pair: lower-bound-ge
module top(input wire [3:0] a, output wire o);
  assign o = a >= 1;
endmodule

// breadth: clean | Comparing an unsigned operand `<= 0` or `> 0` tests whether the operand is zero or non-zero and is not constant.
module top(input wire [3:0] a, output wire o, p);
  assign o = a <= 0;
  assign p = a > 0;
endmodule

// breadth: reports | A bounded unsigned operand of width W compared `> 2^W - 1` is always false.
// pair: upper-bound-gt
module top(input wire [3:0] a, output wire o);
  assign o = a > 15;
endmodule

// breadth: clean | Comparing that 4-bit unsigned operand `> 14` is true when `a == 15` and false otherwise.
// pair: upper-bound-gt
module top(input wire [3:0] a, output wire o);
  assign o = a > 14;
endmodule

// breadth: reports | A bounded unsigned operand of width W compared `<= 2^W - 1` is always true.
// pair: upper-bound-le
module top(input wire [3:0] a, output wire o);
  assign o = a <= 15;
endmodule

// breadth: clean | Comparing that 4-bit unsigned operand `<= 14` is false when `a == 15`.
// pair: upper-bound-le
module top(input wire [3:0] a, output wire o);
  assign o = a <= 14;
endmodule

// breadth: clean | Comparing a 4-bit unsigned operand `< 15` or `>= 15` distinguishes 15 from 0..14 and is not constant.
module top(input wire [3:0] a, output wire o, p);
  assign o = a < 15;
  assign p = a >= 15;
endmodule

// breadth: reports | A one-bit unsigned operand compared `<= 1` is always true.
// pair: one-bit-limit
module top(input wire f, output wire o);
  assign o = f <= 1;
endmodule

// breadth: clean | The same one-bit operand compared `< 1` tests for zero.
// pair: one-bit-limit
module top(input wire f, output wire o);
  assign o = f < 1;
endmodule

// breadth: clean | Constants strictly outside `[0, 2^W - 1]` belong to COMPARISON_WIDTH_MISMATCH rather than this boundary rule.
module top(input wire [3:0] a, output wire o, p);
  assign o = a > 16;
  assign p = a < -1;
endmodule

// breadth: reports | When the constant zero is on the left, the mirrored operators `0 > a` and `0 <= a` are always constant.
// expect: 2
// pair: mirrored-lower-bound
module top(input wire [3:0] a, output wire o, p);
  assign o = 0 > a;
  assign p = 0 <= a;
endmodule

// breadth: clean | With the constant `1` on the left, `1 > a` and `1 <= a` vary with `a`.
// pair: mirrored-lower-bound
module top(input wire [3:0] a, output wire o, p);
  assign o = 1 > a;
  assign p = 1 <= a;
endmodule

// breadth: reports | When the upper-limit constant is on the left, the mirrored operators `15 < a` and `15 >= a` are always constant.
// expect: 2
// pair: mirrored-upper-bound
module top(input wire [3:0] a, output wire o, p);
  assign o = 15 < a;
  assign p = 15 >= a;
endmodule

// breadth: clean | With `14` on the left, `14 < a` and `14 >= a` vary with `a`.
// pair: mirrored-upper-bound
module top(input wire [3:0] a, output wire o, p);
  assign o = 14 < a;
  assign p = 14 >= a;
endmodule

// breadth: clean | Equality and inequality against the range limits (`a == 0`, `a != 15`) are valid boundary tests.
module top(input wire [3:0] a, output wire o, p);
  assign o = a == 0;
  assign p = a != 15;
endmodule

// breadth: clean | A signed operand can be negative, so `sa < 0` and `sa >= 0` are genuine sign checks.
// pair: unsigned-versus-signed-lower-bound
module top(input wire signed [3:0] sa, output wire o);
  assign o = sa < 0;
endmodule

// breadth: reports | The same `< 0` comparison on an unsigned operand is always false.
// pair: unsigned-versus-signed-lower-bound
module top(input wire [3:0] a, output wire o);
  assign o = a < 0;
endmodule

// breadth: reports | Sized literals at `0` and `2^W - 1` fold to the same boundary constants as unsized literals.
// expect: 2
module top(input wire [3:0] a, output wire o, p);
  assign o = a < 4'd0;
  assign p = a <= 4'hF;
endmodule

// breadth: reports | A concatenation is width-bounded to the sum of its member widths, so comparing it against `0` or `2^W - 1` is always constant.
// expect: 2
module top(input wire [1:0] a, b, output wire o, p);
  assign o = {a, b} < 0;
  assign p = {a, b} > 15;
endmodule

// breadth: reports | An unsigned addition is still non-negative, so comparing `(a + b) < 0` is always false.
// pair: computed-lower-versus-upper-bound
module top(input wire [3:0] a, b, output wire o);
  assign o = (a + b) < 0;
endmodule

// breadth: clean | An addition is evaluated at the context width (32 bits against unsized `15`) and can produce a carry up to 30, so `(a + b) > 15` is not constant.
// pair: computed-lower-versus-upper-bound
module top(input wire [3:0] a, b, output wire o);
  assign o = (a + b) > 15;
endmodule

// breadth: gap | An unsigned constant symbol compared `>= 0` is always true whatever its value, but the rule skips comparisons with constant symbols, so it does not report it.
module top(output wire o);
  localparam [3:0] P = 4'd3;
  assign o = P >= 0;
endmodule

// breadth: reports | A vector whose width comes from a parameter default is checked against `2^W - 1` at that default width.
// pair: parameterized-vector-width
module top #(parameter W = 4)(input wire [W-1:0] a, output wire o);
  assign o = a > 15;
endmodule

// breadth: clean | When the parameter default makes the vector wider, `15` is an interior value rather than the upper limit.
// pair: parameterized-vector-width
module top #(parameter W = 8)(input wire [W-1:0] a, output wire o);
  assign o = a > 15;
endmodule

// breadth: reports | A generate branch selected by default parameter values is checked.
// pair: generate-branch-selected
module top #(parameter W = 4)(input wire [W-1:0] a, output wire o);
  if (W == 4) begin : g
    assign o = a > 15;
  end
endmodule

// breadth: clean | A generate branch switched off by default parameter values is skipped.
// pair: generate-branch-selected
module top #(parameter W = 4)(input wire [W-1:0] a, output wire o);
  if (W == 8) begin : g
    assign o = a > 15;
  end
endmodule

// breadth: gap | A part-select is unsigned and bounded to its slice width, so `a[3:0] > 15` is always false; the rule does not report it.
module top(input wire [7:0] a, output wire o);
  assign o = a[3:0] > 15;
endmodule

// breadth: gap | A part-select is unsigned, so `a[3:0] < 0` is always false; the rule does not report it.
module top(input wire [7:0] a, output wire o);
  assign o = a[3:0] < 0;
endmodule

// breadth: gap | A signed 4-bit operand can never exceed 7, so this is always false; no rule reports it.
module top(input wire signed [3:0] sa, output wire o);
  assign o = sa > 7;
endmodule

// breadth: gap | A signed 4-bit operand is never below -8, so this is always true; the rule does not report it.
module top(input wire signed [3:0] sa, output wire o);
  assign o = sa >= -8;
endmodule
