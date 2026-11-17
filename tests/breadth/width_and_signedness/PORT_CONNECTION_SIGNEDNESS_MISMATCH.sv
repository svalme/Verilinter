// breadth: reports | Connecting an unsigned expression to a signed child input port is reported.
// pair: port-signed-net-unsigned
module child(input logic signed [3:0] p);
endmodule
module top(input logic [3:0] u);
  child inst(.p(u));
endmodule

// breadth: clean | Connecting a signed expression to a signed child input port is not reported.
// pair: port-signed-net-unsigned
module child(input logic signed [3:0] p);
endmodule
module top(input logic signed [3:0] s);
  child inst(.p(s));
endmodule

// breadth: reports | Connecting a signed expression to an unsigned child input port is reported.
// pair: port-unsigned-net-signed
module child(input logic [3:0] p);
endmodule
module top(input logic signed [3:0] s);
  child inst(.p(s));
endmodule

// breadth: clean | Connecting an unsigned expression to an unsigned child input port is not reported.
// pair: port-unsigned-net-signed
module child(input logic [3:0] p);
endmodule
module top(input logic [3:0] u);
  child inst(.p(u));
endmodule

// breadth: reports | Connecting an unsigned net to a signed child output port is reported.
// pair: output-port-signed-mismatch
module child(output logic signed [3:0] p);
  assign p = 4'sb0000;
endmodule
module top(output logic [3:0] o);
  logic [3:0] u;
  child inst(.p(u));
  assign o = u;
endmodule

// breadth: clean | Connecting a signed net to a signed child output port is not reported.
// pair: output-port-signed-mismatch
module child(output logic signed [3:0] p);
  assign p = 4'sb0000;
endmodule
module top(output logic signed [3:0] o);
  logic signed [3:0] s;
  child inst(.p(s));
  assign o = s;
endmodule

// breadth: clean | Port connection signedness mismatch in an inactive generate branch is ignored.
module child(input logic signed [3:0] p);
endmodule
module top(input logic [3:0] u);
  if (0) begin : g
    child inst(.p(u));
  end
endmodule

// breadth: reports | A sized unsigned literal connected to a signed port is reported.
module child(input logic signed [3:0] p);
endmodule
module top(output logic o);
  child u(.p(4'd5));
  assign o = 1'b0;
endmodule

// breadth: reports | An unsigned expression connected to a signed port is reported.
module child(input logic signed [3:0] p);
endmodule
module top(input logic [3:0] a, input logic [3:0] b, output logic o);
  child u(.p(a + b));
  assign o = 1'b0;
endmodule

// breadth: reports | A positional connection is checked like a named one.
module child(input logic signed [3:0] p);
endmodule
module top(input logic [3:0] a, output logic o);
  child u(a);
  assign o = 1'b0;
endmodule

// breadth: reports | A concatenation is unsigned, so connecting it to a signed port is reported.
module child(input logic signed [3:0] p);
endmodule
module top(input logic [3:0] a, output logic o);
  child u(.p({a}));
  assign o = 1'b0;
endmodule

// breadth: reports | An unsigned net connected to a signed inout port is reported.
module child(inout wire signed [3:0] p);
endmodule
module top(inout wire [3:0] io);
  child u(.p(io));
endmodule

// breadth: reports | A signedness mismatch is reported when the widths also differ.
module child(input logic [7:0] p);
endmodule
module top(input logic signed [3:0] s, output logic o);
  child u(.p(s));
  assign o = 1'b0;
endmodule

// breadth: clean | A $signed cast on the connected expression satisfies signedness matching.
module child(input logic signed [3:0] p);
endmodule
module top(input logic [3:0] a, output logic o);
  child u(.p($signed(a)));
  assign o = 1'b0;
endmodule

// breadth: gap | The signedness of a part-select is not recovered, so an unsigned part-select connected to a signed port is missed.
module child(input logic signed [3:0] p);
endmodule
module top(input logic [7:0] a, output logic o);
  child u(.p(a[3:0]));
  assign o = 1'b0;
endmodule

// breadth: gap | A wildcard connection pairs an unsigned net with a signed port of the same name, but the pairing is not checked.
module child(input logic signed [3:0] p);
endmodule
module top(input logic [3:0] p, output logic o);
  child u(.*);
  assign o = 1'b0;
endmodule
