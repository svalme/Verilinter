// breadth: reports | An instance output driving an internal net that is never read outside the connection is reported.
// pair: instance-output-read
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  logic a;
  child u(.p(a));
  assign o = 1'b0;
endmodule

// breadth: clean | An instance output driving an internal net that is read within the module is not reported.
// pair: instance-output-read
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  logic a;
  child u(.p(a));
  assign o = a;
endmodule

// breadth: reports | An instance output connected to an unread local net is reported even when an output port exists.
// pair: instance-output-to-port
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  logic a;
  child u(.p(a));
  assign o = 1'b1;
endmodule

// breadth: clean | Forwarding an instance output directly to an enclosing module output port is an allowed pass-through.
// pair: instance-output-to-port
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  child u(.p(o));
endmodule

// breadth: clean | An instance input connection is not an instance output driver.
module child(input logic p);
endmodule
module top(output logic o);
  logic a;
  assign a = 1'b0;
  child u(.p(a));
  assign o = 1'b0;
endmodule

// breadth: clean | An instance output wired into another instance input is read outside the driving connection.
module prod(output logic p);
  assign p = 1'b0;
endmodule
module cons(input logic q);
endmodule
module top(output logic o);
  logic a;
  prod u_prod(.p(a));
  cons u_cons(.q(a));
  assign o = 1'b0;
endmodule

// breadth: clean | An open instance output connection drives no net and is not reported.
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  child u(.p());
  assign o = 1'b0;
endmodule

// breadth: clean | An instance output net read through a hierarchical path has a read outside the connection.
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  logic a;
  child u(.p(a));
  if (1) begin : g
    assign o = top.a;
  end
endmodule

// breadth: clean | Forwarding an instance output to an enclosing inout port is an allowed pass-through.
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(inout wire io);
  child u(.p(io));
endmodule

// breadth: gap | An instance output driving a bit-select of an unread net is unread outside the connection.
// expect: 1
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  logic [3:0] bus;
  child u(.p(bus[0]));
  assign o = 1'b0;
endmodule

// breadth: gap | An instance output connected via wildcard to an unread net is unread outside the connection.
// expect: 1
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  logic p;
  child u(.*);
  assign o = 1'b0;
endmodule

// breadth: reports | Multiple instance outputs driving unread nets are each reported.
// expect: 2
module child(output logic p, output logic q);
  assign p = 1'b0;
  assign q = 1'b0;
endmodule
module top(output logic o);
  logic a, b;
  child u(.p(a), .q(b));
  assign o = 1'b0;
endmodule

// breadth: reports | A whole unread vector driven by an instance output is reported.
module child(output logic [3:0] p);
  assign p = '0;
endmodule
module top(output logic o);
  logic [3:0] bus;
  child u(.p(bus));
  assign o = 1'b0;
endmodule

// breadth: reports | An instance array output driving an unread net is reported.
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  logic [1:0] a;
  child u [1:0] (.p(a));
  assign o = 1'b0;
endmodule

// breadth: reports | A net named with unused is still reported, because the name does not show the output is not needed.
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  logic unused_a;
  child u(.p(unused_a));
  assign o = 1'b0;
endmodule

// breadth: clean | A net read only in an explicit sensitivity list is read outside the connection.
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  logic a;
  child u(.p(a));
  always @(a) o = 1'b1;
endmodule

// breadth: clean | A net read only in a concurrent assertion is read outside the connection.
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(input logic clk, output logic o);
  logic a;
  child u(.p(a));
  assert property (@(posedge clk) a);
  assign o = 1'b0;
endmodule

// breadth: gap | A net driven by two instance outputs and never read is unread outside the connections; only the driver conflict is reported.
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  wire a;
  child u1(.p(a));
  child u2(.p(a));
  assign o = 1'b0;
endmodule
