// breadth: reports | Assigning an unsigned expression to a signed target without explicit cast is reported.
// pair: unsigned-to-signed
module top(input logic [3:0] u, output logic signed [3:0] s);
  assign s = u;
endmodule

// breadth: clean | Assigning a signed expression to a signed target is not reported.
// pair: unsigned-to-signed
module top(input logic signed [3:0] a, output logic signed [3:0] s);
  assign s = a;
endmodule

// breadth: reports | Assigning a signed expression to an unsigned target without explicit cast is reported.
// pair: signed-to-unsigned
module top(input logic signed [3:0] s, output logic [3:0] u);
  assign u = s;
endmodule

// breadth: clean | Assigning an unsigned expression to an unsigned target is not reported.
// pair: signed-to-unsigned
module top(input logic [3:0] a, output logic [3:0] u);
  assign u = a;
endmodule

// breadth: clean | An explicit signed cast on an unsigned expression satisfies signedness matching.
module top(input logic [3:0] u, output logic signed [3:0] s);
  assign s = signed'(u);
endmodule

// breadth: clean | An explicit unsigned cast on a signed expression satisfies signedness matching.
module top(input logic signed [3:0] s, output logic [3:0] u);
  assign u = unsigned'(s);
endmodule

// breadth: clean | Procedural nonblocking assignment with matching signed types is not reported.
// pair: procedural-signedness
module top(input logic clk, input logic signed [3:0] i, output logic signed [3:0] o);
  always_ff @(posedge clk) begin
    o <= i;
  end
endmodule

// breadth: reports | Procedural nonblocking assignment of an unsigned value to a signed target is reported.
// pair: procedural-signedness
module top(input logic clk, input logic [3:0] u, output logic signed [3:0] s);
  always_ff @(posedge clk) begin
    s <= u;
  end
endmodule

// breadth: reports | A blocking procedural assignment of an unsigned value to a signed target is reported.
module top(input logic [3:0] u, output logic signed [3:0] s);
  always_comb s = u;
endmodule

// breadth: reports | A sized unsigned literal assigned to a signed target is reported.
module top(output logic signed [3:0] s);
  assign s = 4'd5;
endmodule

// breadth: reports | A signed sized literal assigned to an unsigned target is reported.
module top(output logic [3:0] u);
  assign u = 4'sd5;
endmodule

// breadth: reports | A mismatch is reported when the target is wider than the source.
module top(input logic [3:0] u, output logic signed [7:0] s);
  assign s = u;
endmodule

// breadth: reports | A conditional expression with one unsigned arm assigned to a signed target is reported.
module top(input logic c, input logic [3:0] u, input logic signed [3:0] a, output logic signed [3:0] s);
  assign s = c ? u : a;
endmodule

// breadth: reports | A signed integer assigned to an unsigned vector is reported.
module top(input integer n, output logic [31:0] u);
  assign u = n;
endmodule

// breadth: reports | A declaration initializer with the wrong signedness is reported.
module top(input logic [3:0] u, output logic signed [3:0] o);
  logic signed [3:0] v = u;
  assign o = v;
endmodule

// breadth: clean | A $signed cast on an unsigned value satisfies signedness matching.
module top(input logic [3:0] u, output logic signed [3:0] s);
  assign s = $signed(u);
endmodule

// breadth: clean | An unsized decimal literal reads the same value signed or unsigned, so it is not compared for signedness.
module top(output logic [3:0] u);
  assign u = 5;
endmodule

// breadth: gap | The signedness of a part-select is not recovered, so an unsigned part-select assigned to a signed target is missed.
module top(input logic [7:0] u, output logic signed [3:0] s);
  assign s = u[3:0];
endmodule

// breadth: gap | The signedness of an arithmetic expression is not recovered, so an unsigned sum assigned to a signed target is missed.
module top(input logic [3:0] u, output logic signed [3:0] s);
  assign s = u + 4'd1;
endmodule
