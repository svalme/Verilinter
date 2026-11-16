// breadth: reports | A relational comparison between a signed and an unsigned operand of the same width evaluates as unsigned.
// pair: relational-operand-signedness
module top(input wire signed [3:0] sa, input wire [3:0] ua, output wire o);
  assign o = sa < ua;
endmodule

// breadth: clean | A relational comparison where both operands are signed.
// pair: relational-operand-signedness
module top(input wire signed [3:0] sa, input wire signed [3:0] sb, output wire o);
  assign o = sa < sb;
endmodule

// breadth: clean | A relational comparison where both operands are unsigned.
module top(input wire [3:0] ua, input wire [3:0] ub, output wire o);
  assign o = ua < ub;
endmodule

// breadth: reports | All four relational operators report when mixing signed and unsigned operands.
// expect: 4
module top(input wire signed [3:0] sa, input wire [3:0] ua, output wire [3:0] o);
  assign o[0] = sa < ua;
  assign o[1] = sa <= ua;
  assign o[2] = sa > ua;
  assign o[3] = sa >= ua;
endmodule

// breadth: reports | An equality comparison between a signed and an unsigned operand of different widths converts the signed operand to unsigned, so it is zero-extended and loses its sign extension.
// pair: equality-width-dependence
module top(input wire signed [3:0] sa, input wire [7:0] ub, output wire o);
  assign o = sa == ub;
endmodule

// breadth: clean | An equality comparison between a signed and an unsigned operand of equal width compares identical bit patterns.
// pair: equality-width-dependence
module top(input wire signed [3:0] sa, input wire [3:0] ua, output wire o);
  assign o = sa == ua;
endmodule

// breadth: clean | An equality comparison between two signed operands of different widths sign-extends the narrower one.
module top(input wire signed [3:0] sa, input wire signed [7:0] sb, output wire o);
  assign o = sa == sb;
endmodule

// breadth: reports | All six equality, case-equality, and wildcard-equality operators report when signedness and width both differ.
// expect: 6
module top(input wire signed [3:0] sa, input wire [7:0] ub, output wire [5:0] o);
  assign o[0] = sa == ub;
  assign o[1] = sa != ub;
  assign o[2] = sa === ub;
  assign o[3] = sa !== ub;
  assign o[4] = sa ==? ub;
  assign o[5] = sa !=? ub;
endmodule

// breadth: reports | A 32-bit signed integer variable compared relationally with a 32-bit unsigned vector mixes signedness at equal width.
// pair: integer-relational-versus-equality-at-32-bits
module top(input wire [31:0] ua, output wire o);
  integer k;
  assign o = ua < k;
endmodule

// breadth: clean | A 32-bit signed integer variable compared for equality with a 32-bit unsigned vector has equal width, so bit patterns compare the same.
// pair: integer-relational-versus-equality-at-32-bits
module top(input wire [31:0] ua, output wire o);
  integer k;
  assign o = ua == k;
endmodule

// breadth: reports | A 32-bit signed integer variable compared for equality with a narrower unsigned vector differs in both signedness and width.
module top(input wire [3:0] ua, output wire o);
  integer k;
  assign o = ua == k;
endmodule

// breadth: clean | Casting the unsigned operand with $signed makes both operands signed.
// pair: explicit-signedness-cast
module top(input wire signed [3:0] sa, input wire [3:0] ua, output wire o);
  assign o = sa < $signed(ua);
endmodule

// breadth: reports | Without the $signed cast on the unsigned operand, the relational comparison mixes signedness.
// pair: explicit-signedness-cast
module top(input wire signed [3:0] sa, input wire [3:0] ua, output wire o);
  assign o = sa < ua;
endmodule

// breadth: clean | Casting the signed operand with $unsigned makes both operands unsigned.
module top(input wire signed [3:0] sa, input wire [3:0] ua, output wire o);
  assign o = $unsigned(sa) < ua;
endmodule

// breadth: clean | A non-negative unsized decimal literal has the same value read as signed or unsigned and is skipped.
module top(input wire [3:0] ua, input wire signed [3:0] sa, output wire o, p);
  assign o = ua < 5;
  assign p = sa < 5;
endmodule

// breadth: clean | A typed parameter or localparam is a compile-time constant symbol whose signedness follows its value and is skipped.
// pair: constant-symbol-versus-variable
module top(input wire [3:0] ua, output wire o);
  localparam int P = 3;
  assign o = ua < P;
endmodule

// breadth: reports | A signed `int` variable is a runtime variable and is reported when compared with an unsigned vector.
// pair: constant-symbol-versus-variable
module top(input wire [3:0] ua, output wire o);
  int v;
  assign o = ua < v;
endmodule

// breadth: clean | An enum member is a compile-time constant symbol and is skipped.
module top(input wire [3:0] ua, output wire o);
  typedef enum int {IDLE = 0, RUN = 1} st_e;
  assign o = ua < IDLE;
endmodule

// breadth: reports | A concatenation is always unsigned by IEEE 1800, even when all of its members are signed.
// pair: concatenation-is-unsigned
module top(input wire signed [3:0] sa, sb, input wire signed [7:0] sc, output wire o);
  assign o = {sa, sb} < sc;
endmodule

// breadth: clean | Comparing that concatenation against an unsigned vector matches signedness.
// pair: concatenation-is-unsigned
module top(input wire signed [3:0] sa, sb, input wire [7:0] uc, output wire o);
  assign o = {sa, sb} < uc;
endmodule

// breadth: reports | A sum of two signed operands is signed, so comparing it with an unsigned operand mixes signedness.
// pair: arithmetic-operand-signedness
module top(input wire signed [3:0] sa, sb, input wire [3:0] ua, output wire o);
  assign o = (sa + sb) < ua;
endmodule

// breadth: clean | A sum of a signed and an unsigned operand is already unsigned, so comparing it with an unsigned operand matches signedness.
// pair: arithmetic-operand-signedness
module top(input wire signed [3:0] sa, input wire [3:0] ua, ub, output wire o);
  assign o = (sa + ua) < ub;
endmodule

// breadth: reports | A sum of a signed and an unsigned operand becomes unsigned, so comparing it with a signed operand mixes signedness.
module top(input wire signed [3:0] sa, input wire [3:0] ua, output wire o);
  assign o = (sa + ua) < sa;
endmodule

// breadth: reports | A bitwise expression of signed operands is signed, so comparing it with an unsigned operand mixes signedness.
module top(input wire signed [3:0] sa, sb, input wire [3:0] ua, output wire o);
  assign o = (sa & sb) < ua;
endmodule

// breadth: reports | A reduction operator yields a 1-bit unsigned result even on a signed operand, so comparing it with a signed operand mixes signedness.
// pair: reduction-result-is-unsigned
module top(input wire signed [3:0] sa, output wire o);
  assign o = (&sa) < sa;
endmodule

// breadth: clean | A reduction result compared with an unsigned signal is unsigned on both sides.
// pair: reduction-result-is-unsigned
module top(input wire signed [3:0] sa, input wire u, output wire o);
  assign o = (&sa) < u;
endmodule

// breadth: reports | A comparison expression yields a 1-bit unsigned result, so comparing it with a signed operand mixes signedness.
module top(input wire signed [3:0] sa, sb, output wire o);
  assign o = (sa == sb) < sa;
endmodule

// breadth: reports | A conditional expression with one signed and one unsigned branch is unsigned, so comparing it with a signed operand mixes signedness.
// pair: ternary-branch-signedness
module top(input wire s, input wire signed [3:0] sa, input wire [3:0] ua, output wire o);
  assign o = (s ? sa : ua) < sa;
endmodule

// breadth: clean | A conditional expression whose branches are both signed remains signed.
// pair: ternary-branch-signedness
module top(input wire s, input wire signed [3:0] sa, sb, output wire o);
  assign o = (s ? sa : sb) < sa;
endmodule

// breadth: gap | A part-select of a signed vector is unsigned, so comparing it relationally with a signed operand mixes signedness; the rule does not report it.
module top(input wire signed [7:0] sa, input wire signed [3:0] sb, output wire o);
  assign o = sa[3:0] < sb;
endmodule

// breadth: gap | A non-negative sized signed literal (4'sd1) has the same value signed or unsigned, so it should be skipped like an unsized literal; the rule still reports it.
// expect: 0
module top(input wire [3:0] ua, output wire o);
  assign o = ua < 4'sd1;
endmodule
