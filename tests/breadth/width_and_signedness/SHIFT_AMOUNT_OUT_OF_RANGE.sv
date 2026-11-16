// breadth: reports | A constant shift amount equal to the shifted operand's bit width shifts every bit out of range.
// pair: shift-amount-at-width-boundary
module top(input wire [3:0] a, output wire [3:0] o);
  assign o = a << 4;
endmodule

// breadth: clean | A constant shift amount one less than the shifted operand's bit width is the largest in-range shift.
// pair: shift-amount-at-width-boundary
module top(input wire [3:0] a, output wire [3:0] o);
  assign o = a << 3;
endmodule

// breadth: clean | A shift amount of zero is in range for any operand of positive width.
module top(input wire [3:0] a, output wire [3:0] o);
  assign o = a << 0;
endmodule

// breadth: reports | A constant shift amount strictly greater than the shifted operand's width is out of range.
module top(input wire [3:0] a, output wire [3:0] o);
  assign o = a << 8;
endmodule

// breadth: reports | All four logical and arithmetic shift operators (`<<`, `>>`, `<<<`, `>>>`) are checked.
// expect: 4
module top(input wire signed [3:0] a, output wire signed [3:0] o0, o1, o2, o3);
  assign o0 = a << 4;
  assign o1 = a >> 4;
  assign o2 = a <<< 4;
  assign o3 = a >>> 4;
endmodule

// breadth: reports | A negative constant shift amount is out of range.
// pair: negative-versus-zero-shift-amount
module top(input wire [3:0] a, output wire [3:0] o);
  assign o = a << -1;
endmodule

// breadth: clean | A non-negative constant shift amount below the operand width is in range.
// pair: negative-versus-zero-shift-amount
module top(input wire [3:0] a, output wire [3:0] o);
  assign o = a << 0;
endmodule

// breadth: reports | A parameter shift amount whose default value is at least the operand width is folded and reported.
// pair: parameter-shift-amount
module top #(parameter S = 4)(input wire [3:0] a, output wire [3:0] o);
  assign o = a << S;
endmodule

// breadth: clean | A parameter shift amount whose default value is below the operand width is in range.
// pair: parameter-shift-amount
module top #(parameter S = 3)(input wire [3:0] a, output wire [3:0] o);
  assign o = a << S;
endmodule

// breadth: reports | A constant arithmetic expression in the shift amount is folded against module parameters.
// pair: constant-expression-shift-amount
module top #(parameter S = 2)(input wire [3:0] a, output wire [3:0] o);
  assign o = a << (S + 2);
endmodule

// breadth: clean | The same constant expression when it folds to an in-range shift amount.
// pair: constant-expression-shift-amount
module top #(parameter S = 2)(input wire [3:0] a, output wire [3:0] o);
  assign o = a << (S + 1);
endmodule

// breadth: clean | A runtime variable shift amount cannot be evaluated at elaboration time and is skipped.
module top(input wire [3:0] a, input wire [7:0] sh, output wire [3:0] o);
  assign o = a << sh;
endmodule

// breadth: reports | A 1-bit scalar shifted by 1 bit reaches its width of 1 and is reported.
// pair: scalar-shift-amount
module top(input wire a, output wire o);
  assign o = a << 1;
endmodule

// breadth: clean | A 1-bit scalar shifted by 0 bits is in range.
// pair: scalar-shift-amount
module top(input wire a, output wire o);
  assign o = a << 0;
endmodule

// breadth: reports | A sized literal as the shifted operand is checked against its declared bit width.
// pair: sized-literal-operand
module top(output wire [3:0] o);
  assign o = 4'b0001 << 4;
endmodule

// breadth: clean | A sized literal shifted by less than its declared width is in range.
// pair: sized-literal-operand
module top(output wire [3:0] o);
  assign o = 4'b0001 << 3;
endmodule

// breadth: clean | An unsized literal is 32 bits, but its shift is sized by the 64-bit target so shifting by 32 moves the bit into the upper half without loss.
module top(output wire [63:0] o);
  assign o = 1 << 32;
endmodule

// breadth: gap | An unsized literal is 32 bits and shifting it by 32 into a 32-bit target loses the bit; the rule does not report it.
module top(output wire [31:0] o);
  assign o = 1 << 32;
endmodule

// breadth: reports | A part-select as the shifted operand has the width of the selected slice.
// pair: part-select-operand
module top(input wire [7:0] a, output wire [3:0] o);
  assign o = a[3:0] >> 4;
endmodule

// breadth: clean | A wider part-select of the same base vector that exceeds the shift amount is in range.
// pair: part-select-operand
module top(input wire [7:0] a, output wire [4:0] o);
  assign o = a[4:0] >> 4;
endmodule

// breadth: reports | A single bit-select has width 1, so shifting it by 1 is out of range.
module top(input wire [7:0] a, output wire o);
  assign o = a[0] << 1;
endmodule

// breadth: reports | A concatenation as the shifted operand has the summed width of its members.
// pair: concatenation-operand
module top(input wire [1:0] a, b, output wire [3:0] o);
  assign o = {a, b} << 4;
endmodule

// breadth: clean | A concatenation shifted by less than the summed width of its members.
// pair: concatenation-operand
module top(input wire [1:0] a, b, output wire [3:0] o);
  assign o = {a, b} << 3;
endmodule

// breadth: reports | A replication as the shifted operand has width equal to the count times the inner width.
module top(input wire [1:0] a, output wire [3:0] o);
  assign o = {2{a}} << 4;
endmodule

// breadth: reports | A nested shift expression preserves the inner shifted operand's width for the outer shift check.
// pair: nested-shift-operand
module top(input wire [3:0] a, output wire [3:0] o);
  assign o = (a << 1) >> 4;
endmodule

// breadth: clean | A nested shift whose outer shift amount is below the inner operand's width.
// pair: nested-shift-operand
module top(input wire [3:0] a, output wire [3:0] o);
  assign o = (a << 1) >> 3;
endmodule

// breadth: reports | A vector whose width comes from a parameter default is checked at that default width.
// pair: parameterized-operand-width
module top #(parameter W = 4)(input wire [W-1:0] a, output wire [W-1:0] o);
  assign o = a >> 4;
endmodule

// breadth: clean | When the parameter default makes the vector wider than the shift amount, the shift is in range.
// pair: parameterized-operand-width
module top #(parameter W = 8)(input wire [W-1:0] a, output wire [W-1:0] o);
  assign o = a >> 4;
endmodule

// breadth: reports | An unpacked array element used as the shifted operand has the element's packed bit width.
module top(output wire [3:0] o);
  logic [3:0] mem [2];
  assign o = mem[0] >> 4;
endmodule

// breadth: reports | A variable declared with a typedef has the typedef's packed bit width when shifted.
module top(output wire [3:0] o);
  typedef logic [3:0] nib_t;
  nib_t a;
  assign o = a >> 4;
endmodule

// breadth: reports | A generate branch selected by default parameter values is checked.
// pair: generate-branch-selected
module top #(parameter W = 4)(input wire [W-1:0] a, output wire [W-1:0] o);
  if (W == 4) begin : g
    assign o = a >> 4;
  end
endmodule

// breadth: clean | A generate branch switched off by default parameter values is skipped.
// pair: generate-branch-selected
module top #(parameter W = 4)(input wire [W-1:0] a, output wire [W-1:0] o);
  if (W == 8) begin : g
    assign o = a >> 4;
  end
endmodule

// breadth: reports | A left shift whose amount reaches the context width loses every bit even when the target is wider than the operand.
module top(input wire [3:0] a, output wire [7:0] o);
  assign o = a << 8;
endmodule

// breadth: reports | A shift inside a concatenation is self-determined, so its operand is not extended and shifting it by its own width loses every bit.
module top(input wire [3:0] a, output wire [7:0] o);
  assign o = {a << 4, 4'b0};
endmodule

// breadth: gap | A left shift is sized by its context: the operand is extended to the wider target before it is shifted, so a shift by the operand's own width moves bits into the extra width and loses nothing; the rule still reports it.
// expect: 0
module top(input wire [3:0] a, output wire [7:0] o);
  assign o = a << 4;
endmodule

// breadth: gap | The same context sizing applies when the shift is an operand of a comparison with a wider vector; the rule still reports it.
// expect: 0
module top(input wire [3:0] a, input wire [7:0] b, output wire o);
  assign o = (a << 4) == b;
endmodule

// breadth: gap | The width of a packed struct member is not recovered, so shifting a 4-bit struct field by 4 is missed.
module top(output wire [3:0] o);
  struct packed { logic [3:0] x; } s;
  assign o = s.x >> 4;
endmodule

// breadth: gap | The return width of a function call is not recovered, so shifting a 4-bit function result by 4 is missed.
module top(input wire x, output wire [3:0] o);
  function automatic [3:0] f(input y);
    f = 4'h1;
  endfunction
  assign o = f(x) >> 4;
endmodule
