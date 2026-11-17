// breadth: reports | An output port read internally but never driven is reported.
// pair: undriven-versus-driven
module top(input logic i, output logic o);
  logic z;
  always_comb begin
    z = o;
  end
endmodule

// breadth: clean | An output port driven by procedural assignment and read internally is not undriven.
// pair: undriven-versus-driven
module top(input logic i, output logic o);
  logic z;
  always_comb begin
    o = i;
    z = o;
  end
endmodule

// breadth: reports | An output port wired only to an instance input port is read and remains undriven.
// pair: instance-port-direction-driver
module child(input logic p);
endmodule
module top(output logic o);
  logic z;
  child u(.p(o));
  always_comb begin
    z = o;
  end
endmodule

// breadth: clean | An output port wired to a child instance output port is driven by that instance.
// pair: instance-port-direction-driver
module child(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  logic z;
  child u(.p(o));
  always_comb begin
    z = o;
  end
endmodule

// breadth: reports | An output port read in continuous logic without any driver is reported.
// pair: unreferenced-versus-read-undriven
module top(output logic o);
  logic z;
  assign z = o;
endmodule

// breadth: clean | An output port that is never read internally belongs to UNUSED_VARIABLE.
// pair: unreferenced-versus-read-undriven
module top(output logic o);
endmodule

// breadth: clean | An input port read but not driven is not an undriven output port.
module top(input logic i, output logic o);
  assign o = i;
endmodule

// breadth: clean | An internal signal read but never written belongs to NO_UNDRIVEN_SIGNAL.
module top(output logic o);
  logic internal_sig;
  assign o = internal_sig;
endmodule

// breadth: clean | An output port driven by continuous assignment is not undriven.
module top(input logic i, output logic o);
  logic z;
  assign o = i;
  assign z = o;
endmodule

// breadth: clean | An output port driven through a hierarchical path from another module is driven.
module writer;
  always_comb top.o = 1'b1;
endmodule
module top(output logic o);
  logic z;
  writer u();
  always_comb z = o;
endmodule

// breadth: clean | An output port driven inside a generate block is driven.
module top(input logic i, output logic o);
  logic z;
  if (1) begin : g
    assign o = i;
  end
  assign z = o;
endmodule

// breadth: reports | Multiple output ports read internally and never driven are each reported.
// expect: 2
module top(output logic o1, output logic o2);
  logic z1, z2;
  always_comb begin
    z1 = o1;
    z2 = o2;
  end
endmodule

// breadth: clean | An output port driven by a clocked block and read internally is not undriven.
module top(input logic clk, input logic i, output logic o);
  logic z;
  always_ff @(posedge clk) o <= i;
  assign z = o;
endmodule

// breadth: clean | A legacy output reg driven by an always block and read internally is not undriven.
module top(input logic i, output reg o);
  reg z;
  always @* begin
    o = i;
    z = o;
  end
endmodule

// breadth: clean | An output port driven through a task output argument is driven.
module top(input logic i, output logic o);
  logic z;
  task automatic t(output logic y);
    y = 1'b1;
  endtask
  always_comb begin
    t(o);
    z = o;
  end
endmodule

// breadth: clean | An output port driven by an initial block is driven.
module top(output logic o);
  logic z;
  initial o = 1'b0;
  assign z = o;
endmodule

// breadth: reports | An output port read only in an assertion and never driven is reported.
module top(input logic clk, output logic o);
  assert property (@(posedge clk) o);
endmodule

// breadth: gap | An output bit that is read but never driven is undriven even when other bits of the port are driven, but only a port with no driver at all is reported.
module top(input logic i, output logic [1:0] o);
  logic z;
  assign o[0] = i;
  assign z = o[1];
endmodule
