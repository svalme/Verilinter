// breadth: reports | Two operands whose declared widths differ are reported, in either direction.
// pair: operand-widths
module top(input wire [3:0] a, input wire [7:0] b, output wire o);
  assign o = a == b;
endmodule

// breadth: clean | Two operands of the same width.
// pair: operand-widths
module top(input wire [3:0] a, input wire [3:0] c, output wire o);
  assign o = a == c;
endmodule

// breadth: reports | Every comparison operator is checked, including the case-equality and wildcard forms.
// expect: 10
module top(input wire [3:0] a, input wire [7:0] b, output wire [9:0] o);
  assign o[0] = a == b;
  assign o[1] = a != b;
  assign o[2] = a < b;
  assign o[3] = a <= b;
  assign o[4] = a > b;
  assign o[5] = a >= b;
  assign o[6] = a === b;
  assign o[7] = a !== b;
  assign o[8] = a ==? b;
  assign o[9] = a !=? b;
endmodule

// breadth: reports | A comparison in a procedural condition is checked like one in a continuous assignment.
module top(input wire [3:0] a, input wire [7:0] b, output reg o);
  always @* begin
    if (a == b) o = 1'b1;
    else o = 1'b0;
  end
endmodule

// breadth: reports | A part-select wider than the other operand.
// pair: select-width
module top(input wire [7:0] b, input wire [3:0] a, output wire o);
  assign o = b[7:2] == a;
endmodule

// breadth: clean | A part-select exactly as wide as the other operand.
// pair: select-width
module top(input wire [7:0] b, input wire [3:0] a, output wire o);
  assign o = b[7:4] == a;
endmodule

// breadth: reports | A single bit compared with a vector.
// pair: bit-select-width
module top(input wire [3:0] a, output wire o);
  assign o = a[3] == a;
endmodule

// breadth: clean | A single bit compared with a one-bit signal.
// pair: bit-select-width
module top(input wire [3:0] a, input wire f, output wire o);
  assign o = a[3] == f;
endmodule

// breadth: reports | A concatenation wider than the other operand.
module top(input wire [3:0] a, input wire [3:0] c, output wire o);
  assign o = {a, c} == a;
endmodule

// breadth: clean | A concatenation exactly as wide as the other operand.
module top(input wire [3:0] a, input wire [3:0] c, input wire [7:0] b, output wire o);
  assign o = {a, c} == b;
endmodule

// breadth: reports | A replication wider than the other operand.
module top(input wire [3:0] a, output wire o);
  assign o = {2{a}} == a;
endmodule

// breadth: reports | A comparison result is one bit, so comparing it with a vector is a width difference.
// pair: comparison-result-width
module top(input wire [3:0] a, input wire [3:0] c, output wire o);
  assign o = (a == c) == a;
endmodule

// breadth: clean | A comparison result compared with a one-bit signal.
// pair: comparison-result-width
module top(input wire [3:0] a, input wire [3:0] c, input wire f, output wire o);
  assign o = (a == c) == f;
endmodule

// breadth: reports | A reduction result is one bit, so comparing it with a vector is a width difference.
// pair: reduction-width
module top(input wire [3:0] a, output wire o);
  assign o = (&a) == a;
endmodule

// breadth: clean | A reduction result compared with a one-bit signal.
// pair: reduction-width
module top(input wire [3:0] a, input wire f, output wire o);
  assign o = (&a) == f;
endmodule

// breadth: reports | A sum of narrow operands compared with a wider vector.
// pair: arithmetic-operand-width
module top(input wire [3:0] a, input wire [3:0] c, input wire [7:0] b, output wire o);
  assign o = (a + c) == b;
endmodule

// breadth: clean | A sum of narrow operands compared with a vector of the operands' own width.
// pair: arithmetic-operand-width
module top(input wire [3:0] a, input wire [3:0] c, output wire o);
  assign o = (a + c) == a;
endmodule

// breadth: clean | A sum with an unsized literal has no recoverable width, so the common `x == y + 1` check is not reported.
module top(input wire [3:0] a, input wire [3:0] c, output wire o);
  assign o = a == c + 1;
endmodule

// breadth: reports | A bitwise result takes its widest operand's width, which differs from the wider vector.
// pair: bitwise-operand-width
module top(input wire [3:0] a, input wire [3:0] c, input wire [7:0] b, output wire o);
  assign o = (a & c) == b;
endmodule

// breadth: clean | A bitwise result compared with a vector of the operands' own width.
// pair: bitwise-operand-width
module top(input wire [3:0] a, input wire [3:0] c, output wire o);
  assign o = (a & c) == a;
endmodule

// breadth: clean | A bitwise expression with a parameter operand is unknown, because the parameter's declared width does not limit its value.
module top(input wire [3:0] a, input wire [3:0] c, output wire o);
  localparam P = 3;
  assign o = (a & P) == c;
endmodule

// breadth: reports | A shifted operand keeps its own width, which differs from the wider vector.
// pair: shift-operand-width
module top(input wire [3:0] a, input wire [7:0] b, output wire o);
  assign o = (a << 1) == b;
endmodule

// breadth: clean | A shifted operand compared with a vector of its own width.
// pair: shift-operand-width
module top(input wire [3:0] a, input wire [3:0] c, output wire o);
  assign o = (a << 1) == c;
endmodule

// breadth: reports | A conditional expression takes its widest branch's width.
module top(input wire f, input wire [3:0] a, input wire [3:0] c, input wire [7:0] b, output wire o);
  assign o = (f ? a : c) == b;
endmodule

// breadth: reports | An element of an unpacked array compared with a narrower vector.
module top(input wire [3:0] a, output wire o);
  logic [7:0] mem [4];
  assign o = mem[0] == a;
endmodule

// breadth: reports | A name declared with a plain typedef has the typedef's width.
module top(input wire [3:0] a, output wire o);
  typedef logic [7:0] byte_t;
  byte_t t;
  assign o = t == a;
endmodule

// breadth: clean | An enum member compared with a variable of the enum type: the width of a named type is not read.
module top(input wire f, output wire o);
  typedef enum logic [1:0] {IDLE, RUN} st_t;
  st_t st;
  assign o = st == IDLE;
endmodule

// breadth: reports | A 32-bit integer variable compared with a narrower counter; widening is accurate by the rule's definition though often intended.
module top(input wire [3:0] a, output wire o);
  integer k;
  assign o = a == k;
endmodule

// breadth: reports | An unsigned operand compared with a literal above its largest value, which can never be equal.
// pair: unsigned-literal-range
module top(input wire [3:0] a, output wire o);
  assign o = a == 16;
endmodule

// breadth: clean | The largest value an unsigned operand can hold.
// pair: unsigned-literal-range
module top(input wire [3:0] a, output wire o);
  assign o = a == 15;
endmodule

// breadth: reports | An ordering comparison against a literal above the largest value is always false.
module top(input wire [3:0] a, output wire o);
  assign o = a > 16;
endmodule

// breadth: clean | In-range unsized literals, including zero, are idiomatic checks.
module top(input wire [3:0] a, output wire o, p);
  assign o = a == 0;
  assign p = a >= 0;
endmodule

// breadth: reports | A negative literal compared with an unsigned operand can never be equal.
// pair: negative-literal-signedness
module top(input wire [3:0] a, output wire o);
  assign o = a == -1;
endmodule

// breadth: clean | A negative literal compared with a signed operand that can hold it.
// pair: negative-literal-signedness
module top(input wire signed [3:0] sa, output wire o);
  assign o = sa == -1;
endmodule

// breadth: reports | A signed operand compared with a literal above its largest value.
// pair: signed-literal-range
module top(input wire signed [3:0] sa, output wire o);
  assign o = sa == 8;
endmodule

// breadth: clean | The largest value a signed operand can hold.
// pair: signed-literal-range
module top(input wire signed [3:0] sa, output wire o);
  assign o = sa == 7;
endmodule

// breadth: reports | A signed operand compared with a literal below its smallest value.
module top(input wire signed [3:0] sa, output wire o);
  assign o = sa == -9;
endmodule

// breadth: reports | The literal may be on the left: it is checked against the other operand's range the same way.
// pair: literal-side
module top(input wire [3:0] a, output wire o);
  assign o = 16 == a;
endmodule

// breadth: clean | An in-range literal on the left.
// pair: literal-side
module top(input wire [3:0] a, output wire o);
  assign o = 0 == a;
endmodule

// breadth: reports | A sized literal wider than the other operand.
// pair: sized-literal-width
module top(input wire [3:0] a, output wire o);
  assign o = a == 5'd0;
endmodule

// breadth: clean | A sized literal of the other operand's width.
// pair: sized-literal-width
module top(input wire [3:0] a, output wire o);
  assign o = a == 4'd0;
endmodule

// breadth: reports | A parameter with a type has the type's width, here 32 bits.
// pair: parameter-typing
module top(input wire [3:0] a, output wire o);
  localparam int P = 3;
  assign o = a == P;
endmodule

// breadth: clean | A parameter with no type or range has the width of its value, which is not known here.
// pair: parameter-typing
module top(input wire [3:0] a, output wire o);
  localparam P = 3;
  assign o = a == P;
endmodule

// breadth: reports | A parameter with a range keeps that range, which is wider than the other operand.
// pair: parameter-range
module top(input wire [3:0] a, output wire o);
  localparam [7:0] P = 3;
  assign o = a == P;
endmodule

// breadth: clean | A parameter with a range as wide as the other operand.
// pair: parameter-range
module top(input wire [3:0] a, output wire o);
  localparam [3:0] P = 3;
  assign o = a == P;
endmodule

// breadth: reports | A vector whose width comes from a parameter default is compared at that width.
// pair: parameter-width-vector
module top #(parameter W = 8)(input wire [W-1:0] x, input wire [3:0] a, output wire o);
  assign o = x == a;
endmodule

// breadth: clean | The same comparison when the parameter default makes the widths equal.
// pair: parameter-width-vector
module top #(parameter W = 4)(input wire [W-1:0] x, input wire [3:0] a, output wire o);
  assign o = x == a;
endmodule

// breadth: reports | A generate branch that the default parameter values select is checked.
// pair: generate-branch-selected
module top #(parameter W = 4)(input wire [W-1:0] x, input wire [7:0] b, output wire o);
  if (W == 4) begin : g
    assign o = x == b;
  end
endmodule

// breadth: clean | A generate branch that the default parameter values switch off is not checked.
// pair: generate-branch-selected
module top #(parameter W = 4)(input wire [W-1:0] x, input wire [7:0] b, output wire o);
  if (W == 1) begin : g
    assign o = x == b;
  end
endmodule

// breadth: gap | The return width of a function call is not recovered, so a result wider than the other operand is missed.
module top(input wire f, input wire [3:0] a, output wire o);
  function automatic [7:0] f1(input y);
    f1 = 8'h1;
  endfunction
  assign o = f1(f) == a;
endmodule

// breadth: gap | The width of a packed struct member is not recovered, so a member wider than the other operand is missed.
module top(input wire [3:0] a, output wire o);
  struct packed { logic [7:0] x; } s;
  assign o = s.x == a;
endmodule
