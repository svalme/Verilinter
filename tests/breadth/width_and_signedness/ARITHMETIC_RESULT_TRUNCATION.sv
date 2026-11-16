// breadth: reports | An addition with an operand wider than the target has arithmetic capacity exceeding the target width.
// pair: add-operand-capacity
module top(input wire [7:0] a, input wire [3:0] b, output wire [3:0] o);
  assign o = a + b;
endmodule

// breadth: clean | An addition of operands as wide as the target is not reported: the rule counts the widest operand and ignores the carry bit (the documented capacity policy).
// pair: add-operand-capacity
module top(input wire [3:0] a, input wire [3:0] b, output wire [3:0] o);
  assign o = a + b;
endmodule

// breadth: reports | A subtraction with an operand wider than the target exceeds the target width.
// pair: sub-operand-capacity
module top(input wire [7:0] a, input wire [3:0] b, output wire [3:0] o);
  assign o = a - b;
endmodule

// breadth: clean | A subtraction whose operands are no wider than the target.
// pair: sub-operand-capacity
module top(input wire [3:0] a, input wire [3:0] b, output wire [3:0] o);
  assign o = a - b;
endmodule

// breadth: reports | A multiplication requires the sum of its operand widths, so two 4-bit operands into a 7-bit target truncate the 8-bit product capacity.
// pair: mul-product-capacity
module top(input wire [3:0] a, input wire [3:0] b, output wire [6:0] o);
  assign o = a * b;
endmodule

// breadth: clean | A target as wide as the sum of the multiplier operand widths holds the full product.
// pair: mul-product-capacity
module top(input wire [3:0] a, input wire [3:0] b, output wire [7:0] o);
  assign o = a * b;
endmodule

// breadth: reports | Chained multiplications sum the widths of every factor on the spine.
// pair: chained-mul-capacity
module top(input wire [3:0] a, b, c, output wire [10:0] o);
  assign o = a * b * c;
endmodule

// breadth: clean | A target as wide as the sum of all three factor widths holds the chained product.
// pair: chained-mul-capacity
module top(input wire [3:0] a, b, c, output wire [11:0] o);
  assign o = a * b * c;
endmodule

// breadth: reports | An addition containing a nested multiplication takes the product's summed capacity.
// pair: nested-mul-in-add
module top(input wire [3:0] a, b, c, output wire [6:0] o);
  assign o = (a * b) + c;
endmodule

// breadth: clean | A target wide enough for the nested product capacity in an addition.
// pair: nested-mul-in-add
module top(input wire [3:0] a, b, c, output wire [7:0] o);
  assign o = (a * b) + c;
endmodule

// breadth: reports | A conditional expression with a multiplication branch whose product capacity exceeds both the simple branch width and the target width.
// pair: ternary-mul-branch
module top(input wire s, input wire [3:0] a, b, output wire [3:0] o);
  assign o = s ? (a * b) : a;
endmodule

// breadth: clean | The same conditional expression when the target is wide enough for the product branch.
// pair: ternary-mul-branch
module top(input wire s, input wire [3:0] a, b, output wire [7:0] o);
  assign o = s ? (a * b) : a;
endmodule

// breadth: clean | A plain signal wider than the target has a simple operand width equal to its natural width, so it is left to ASSIGNMENT_TRUNCATION.
// pair: arithmetic-versus-plain-transfer
module top(input wire [7:0] a, input wire [3:0] b, output wire [3:0] o);
  assign o = a;
endmodule

// breadth: reports | Combining that wide signal in an addition makes it a computed expression with no simple operand width, so this rule reports it.
// pair: arithmetic-versus-plain-transfer
module top(input wire [7:0] a, input wire [3:0] b, output wire [3:0] o);
  assign o = a + b;
endmodule

// breadth: gap | A signedness cast around a product hides the lost bits: the product is cut to the target width exactly as in the uncast form, but neither this rule nor ASSIGNMENT_TRUNCATION reports it.
module top(input wire [3:0] a, b, output wire [3:0] o);
  assign o = $signed(a * b);
endmodule

// breadth: reports | Casting the individual factors before multiplying keeps the full-product capacity check.
module top(input wire [3:0] a, b, output wire [3:0] o);
  assign o = $signed(a) * $signed(b);
endmodule

// breadth: reports | A bitwise binary expression has no simple expression width and its natural width is the widest operand, which exceeds the target.
// pair: bitwise-operand-capacity
module top(input wire [7:0] a, input wire [3:0] b, output wire [3:0] o);
  assign o = a & b;
endmodule

// breadth: clean | A bitwise binary expression whose widest operand fits in the target.
// pair: bitwise-operand-capacity
module top(input wire [3:0] a, input wire [3:0] b, output wire [3:0] o);
  assign o = a & b;
endmodule

// breadth: reports | A bitwise negation takes its operand's width and is reported when that exceeds the target.
module top(input wire [7:0] a, output wire [3:0] o);
  assign o = ~a;
endmodule

// breadth: clean | A bitwise expression with a parameter operand has unknown natural width because the parameter's declared width does not bound its value.
module top(input wire [7:0] a, output wire [3:0] o);
  localparam int P = 3;
  assign o = a & P;
endmodule

// breadth: reports | An addition with a sized literal uses the literal's declared width.
module top(input wire [7:0] a, output wire [3:0] o);
  assign o = a + 8'd1;
endmodule

// breadth: gap | An addition with an unsized literal is skipped, but its variable operand is already wider than the target, so the sum loses bits whatever the literal is; the rule does not report it.
module top(input wire [7:0] a, output wire [3:0] o);
  assign o = a + 1;
endmodule

// breadth: reports | A shift expression inside an addition contributes the shifted operand's width.
module top(input wire [7:0] a, input wire [3:0] b, output wire [3:0] o);
  assign o = (a << 1) + b;
endmodule

// breadth: reports | A concatenation inside an addition contributes the sum of its member widths.
module top(input wire [3:0] a, b, c, output wire [3:0] o);
  assign o = {a, b} + c;
endmodule

// breadth: reports | A declarator initializer is checked against the declared width.
module top(input wire [3:0] a, b);
  wire [3:0] o = a * b;
endmodule

// breadth: reports | A port default expression is checked against the port's declared width.
module top(input wire [3:0] a = 4'd2 * 4'd3, output wire [3:0] o);
  assign o = a;
endmodule

// breadth: reports | A nonblocking assignment is checked against its target width.
// pair: assignment-operator
module top(input logic clk, input logic [7:0] a, input logic [3:0] b, output logic [3:0] o);
  always_ff @(posedge clk) o <= a + b;
endmodule

// breadth: clean | A compound assignment is excluded because its right-hand side is an operand rather than the full assigned expression.
// pair: assignment-operator
module top(input logic clk, input logic [7:0] a, output logic [3:0] o);
  always_ff @(posedge clk) o += a;
endmodule

// breadth: reports | A part-select target is checked at the selected slice width rather than the base signal width.
module top(input wire [3:0] a, b, output wire [7:0] o);
  assign o[3:0] = a * b;
  assign o[7:4] = 4'd0;
endmodule

// breadth: reports | A concatenated target narrower than the arithmetic capacity is reported.
// pair: concatenated-target-width
module top(input wire [3:0] a, b, output wire [2:0] x, y);
  assign {x, y} = a * b;
endmodule

// breadth: clean | A concatenated target whose combined width matches the arithmetic capacity.
// pair: concatenated-target-width
module top(input wire [3:0] a, b, output wire [3:0] x, y);
  assign {x, y} = a * b;
endmodule

// breadth: reports | An unpacked array element used as an arithmetic operand contributes the element width.
module top(input wire [3:0] b, output wire [3:0] o);
  logic [7:0] mem [4];
  assign o = mem[0] + b;
endmodule

// breadth: reports | A variable declared with a typedef contributes the typedef's packed width in arithmetic.
module top(input wire [3:0] b, output wire [3:0] o);
  typedef logic [7:0] byte_t;
  byte_t a;
  assign o = a + b;
endmodule

// breadth: reports | A generate branch selected by default parameter values is checked.
// pair: generate-branch-selected
module top #(parameter W = 4)(input wire [W-1:0] a, b, output wire [3:0] o);
  if (W == 4) begin : g
    assign o = a * b;
  end
endmodule

// breadth: clean | A generate branch switched off by default parameter values is skipped.
// pair: generate-branch-selected
module top #(parameter W = 4)(input wire [W-1:0] a, b, output wire [3:0] o);
  if (W == 8) begin : g
    assign o = a * b;
  end
endmodule

// breadth: gap | The return width of a function call is not recovered, so an addition with a wide function result is missed.
module top(input wire x, input wire [3:0] b, output wire [3:0] o);
  function automatic [7:0] f(input y);
    f = 8'h1;
  endfunction
  assign o = f(x) + b;
endmodule

// breadth: gap | The width of a packed struct member is not recovered, so an addition with a wide struct field is missed.
module top(input wire [3:0] b, output wire [3:0] o);
  struct packed { logic [7:0] x; } s;
  assign o = s.x + b;
endmodule
