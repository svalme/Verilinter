// breadth: reports | A plain signal wider than its target loses its upper bits.
// pair: truncating-versus-extending
module top(input wire [7:0] a, output wire [3:0] o);
  assign o = a;
endmodule

// breadth: clean | The same assignment with the widths swapped extends the value; this rule reports only the lossy direction.
// pair: truncating-versus-extending
module top(input wire [3:0] a, output wire [7:0] o);
  assign o = a;
endmodule

// breadth: clean | A right-hand side exactly as wide as its target.
module top(input wire [3:0] a, output wire [3:0] o);
  assign o = a;
endmodule

// breadth: reports | A declarator initializer wider than the declared net.
module top(input wire [7:0] a);
  wire [3:0] o = a;
endmodule

// breadth: reports | A vector assigned to a one-bit target.
module top(input wire [7:0] a, output wire o);
  assign o = a;
endmodule

// breadth: reports | A part-select that is wider than the target.
// pair: select-width
module top(input wire [7:0] a, output wire [3:0] o);
  assign o = a[7:2];
endmodule

// breadth: clean | A part-select exactly as wide as the target.
// pair: select-width
module top(input wire [7:0] a, output wire [3:0] o);
  assign o = a[7:4];
endmodule

// breadth: reports | A concatenation whose parts add up to more than the target.
module top(input wire [3:0] a, b, output wire [3:0] o);
  assign o = {a, b};
endmodule

// breadth: reports | A replication wider than the target.
module top(input wire a, output wire [3:0] o);
  assign o = {8{a}};
endmodule

// breadth: reports | A source whose width comes from a parameter default is compared at that width.
module top #(parameter W = 8)(input wire [W-1:0] a, output wire [3:0] o);
  assign o = a;
endmodule

// breadth: clean | A source and a target that both take their width from the same parameter.
module top #(parameter W = 8)(input wire [W-1:0] a, output wire [W-1:0] o);
  assign o = a;
endmodule

// breadth: reports | A conditional expression takes the width of its widest branch.
module top(input wire s, input wire [7:0] a, input wire [3:0] b, output wire [3:0] o);
  assign o = s ? a : b;
endmodule

// breadth: reports | A shifted operand that is already wider than the target loses bits.
// pair: shift-operand-width
module top(input wire [7:0] r, output wire [3:0] o);
  assign o = r << 1;
endmodule

// breadth: clean | A left shift of a narrower operand is sized by the target, so the wider target holds the result.
// pair: shift-operand-width
module top(input wire [3:0] a, output wire [7:0] o);
  assign o = a << 2;
endmodule

// breadth: reports | A signedness cast keeps the operand width, so narrowing through it still truncates.
// pair: cast-direction
module top(input wire [7:0] a, output wire [3:0] o);
  assign o = $signed(a);
endmodule

// breadth: clean | A signedness cast that widens a value on purpose.
// pair: cast-direction
module top(input wire [3:0] a, output wire [7:0] o);
  assign o = $signed(a);
endmodule

// breadth: reports | A sized literal wider than the target.
module top(output wire [3:0] o);
  assign o = 8'hFF;
endmodule

// breadth: clean | An unsized literal and an unsized fill literal have no width of their own, so they fit any target.
module top(output wire o, output wire [3:0] p);
  assign o = 1;
  assign p = '0;
endmodule

// breadth: reports | A 32-bit integer variable assigned to a narrow register.
module top(output logic [1:0] o);
  integer k;
  always_comb begin
    k = 1;
    o = k;
  end
endmodule

// breadth: reports | A 32-bit typed parameter assigned to a narrow net.
module top #(parameter int P = 3)(output wire [3:0] o);
  assign o = P;
endmodule

// breadth: reports | An element of an unpacked array that is wider than the target.
module top(output wire [7:0] x, input logic [15:0] one [4]);
  assign x = one[1];
endmodule

// breadth: reports | The target is a part-select, so its width is the selected range.
module top(input wire [7:0] a, output wire [7:0] o);
  assign o[3:0] = a;
endmodule

// breadth: reports | A concatenated target is as wide as its parts together, and the right-hand side is wider.
module top(input wire [15:0] a, output wire [3:0] x, y);
  assign {x, y} = a;
endmodule

// breadth: clean | A concatenated target as wide as the right-hand side.
module top(input wire [7:0] a, output wire [3:0] x, y);
  assign {x, y} = a;
endmodule

// breadth: reports | A nonblocking assignment in a clocked block is checked like a continuous one.
// pair: assignment-operator
module top(input logic clk, input logic [7:0] a, output logic [3:0] o);
  always_ff @(posedge clk) o <= a;
endmodule

// breadth: clean | A compound assignment is excluded: its right-hand side is an operand, not the value transferred.
// pair: assignment-operator
module top(input logic clk, input logic [7:0] a, output logic [3:0] o);
  always_ff @(posedge clk) o += a;
endmodule

// breadth: reports | A generate branch that the default parameter values select is checked.
// pair: generate-branch-selected
module top #(parameter W = 4)(input wire [W-1:0] d, output wire o);
  if (W == 4) begin : g
    assign o = d;
  end
endmodule

// breadth: clean | A generate branch that the default parameter values switch off is not checked; its width belongs to another parameter value.
// pair: generate-branch-selected
module top #(parameter W = 4)(input wire [W-1:0] d, output wire o);
  if (W == 1) begin : g
    assign o = d;
  end
endmodule

// breadth: reports | A plain name wider than the target.
// pair: plain-versus-arithmetic
module top(input wire [7:0] a, b, output wire [3:0] o);
  assign o = b;
endmodule

// breadth: clean | An addition of wide operands into a narrow target belongs to ARITHMETIC_RESULT_TRUNCATION, which reports it.
// pair: plain-versus-arithmetic
module top(input wire [7:0] a, b, output wire [3:0] o);
  assign o = a + b;
endmodule

// breadth: clean | A bitwise expression of wide operands is also left to ARITHMETIC_RESULT_TRUNCATION.
module top(input wire [7:0] a, b, output wire [3:0] o);
  assign o = a & b;
endmodule

// breadth: clean | Operators whose result is one bit never exceed a one-bit target.
module top(input wire [7:0] a, b, output wire r, e, s);
  assign r = &a;
  assign e = a == b;
  assign s = a[3];
endmodule

// breadth: gap | The return width of a function call is not recovered, so a result wider than the target is missed.
module top(input wire x, output wire [3:0] o);
  function automatic [7:0] f(input y);
    f = 8'h1;
  endfunction
  assign o = f(x);
endmodule
