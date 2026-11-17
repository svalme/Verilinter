// breadth: reports | An unsized decimal literal on the right-hand side of a continuous assignment is reported.
// pair: continuous-assign-unsized
module top(output logic [7:0] o);
  assign o = 42;
endmodule

// breadth: clean | A sized decimal literal on the right-hand side of a continuous assignment is not reported.
// pair: continuous-assign-unsized
module top(output logic [7:0] o);
  assign o = 8'd42;
endmodule

// breadth: reports | An unsized decimal literal on the right-hand side of a procedural assignment is reported.
// pair: procedural-assign-unsized
module top(output logic [7:0] o);
  always_comb o = 10;
endmodule

// breadth: clean | A sized decimal literal on the right-hand side of a procedural assignment is not reported.
// pair: procedural-assign-unsized
module top(output logic [7:0] o);
  always_comb o = 8'd10;
endmodule

// breadth: reports | An unsized decimal literal used as a variable declaration initializer is reported.
// pair: declarator-initializer-unsized
module top(output logic [7:0] o);
  logic [7:0] v = 5;
  assign o = v;
endmodule

// breadth: clean | A sized literal used as a variable declaration initializer is not reported.
// pair: declarator-initializer-unsized
module top(output logic [7:0] o);
  logic [7:0] v = 8'd5;
  assign o = v;
endmodule

// breadth: clean | An unsized integer literal defining a parameter constant is allowed.
module top #(parameter WIDTH = 16)(input logic [WIDTH-1:0] i, output logic o);
  assign o = i[0];
endmodule

// breadth: clean | An unsized literal inside a for loop step expression is allowed.
module top(input logic [3:0] in_v, output logic [3:0] out_v);
  always_comb begin
    for (int i = 0; i < 4; i = i + 1) begin
      out_v[i] = in_v[i];
    end
  end
endmodule

// breadth: clean | An unbased unsized '0 literal is not an unsized decimal literal.
module top(output logic [7:0] o);
  assign o = '0;
endmodule

// breadth: reports | An unsized decimal literal assigned with a nonblocking assignment in a clocked block is reported.
// pair: nonblocking-unsized
module top(input logic clk, output logic [3:0] o);
  always_ff @(posedge clk) o <= 0;
endmodule

// breadth: clean | A sized literal assigned with a nonblocking assignment in a clocked block is not reported.
// pair: nonblocking-unsized
module top(input logic clk, output logic [3:0] o);
  always_ff @(posedge clk) o <= 4'd0;
endmodule

// breadth: clean | An unsized literal that is only an operand of an expression is not the direct right-hand side of the assignment and is not reported.
module top(input logic [3:0] a, output logic [3:0] o);
  assign o = a + 1;
endmodule

// breadth: clean | An unsized literal in a comparison is not the direct right-hand side of an assignment and is not reported.
module top(input logic [3:0] a, output logic o);
  assign o = (a == 3);
endmodule

// breadth: gap | An unsized literal in both arms of a conditional expression is assigned with an inferred width just as a direct right-hand side is, but only a direct right-hand side is reported.
module top(input logic c, output logic [3:0] o);
  assign o = c ? 1 : 0;
endmodule

// breadth: gap | A negated unsized literal is assigned with an inferred width just as a plain one is, but only the plain literal is reported.
module top(output logic signed [3:0] o);
  assign o = -1;
endmodule

// breadth: gap | An unsized based literal has the same inferred 32-bit width as an unsized decimal one, but only decimal literals are reported.
module top(output logic [7:0] o);
  assign o = 'd5;
endmodule
