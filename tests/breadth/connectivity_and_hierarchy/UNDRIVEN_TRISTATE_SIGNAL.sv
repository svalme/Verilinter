// breadth: reports | An internal wire driven only by a conditional tri-state continuous assignment is reported.
// pair: tristate-vs-non-tristate-driver
module top(input logic en, input logic d, output logic q);
  wire bus;
  assign bus = en ? d : 1'bz;
  assign q = bus;
endmodule

// breadth: clean | An internal wire driven by an unconditional non-tri-state continuous assignment is not reported.
// pair: tristate-vs-non-tristate-driver
module top(input logic d, output logic q);
  wire bus;
  assign bus = d;
  assign q = bus;
endmodule

// breadth: reports | An internal net driven only by a single tri-state assign is reported.
// pair: internal-wire-vs-port-net
module top(input logic en, input logic [3:0] d, output logic [3:0] q);
  wire [3:0] bus;
  assign bus = en ? d : 4'bzzzz;
  assign q = bus;
endmodule

// breadth: clean | An inout module port driven by a single tri-state assignment is not reported.
// pair: internal-wire-vs-port-net
module top(input logic en, input logic [3:0] d, inout wire [3:0] bus);
  assign bus = en ? d : 4'bzzzz;
endmodule

// breadth: reports | An internal wire driven only by a tri-state assign and not connected to an instance is reported.
// pair: internal-wire-vs-instance-connection
module top(input logic en, input logic d, output logic q);
  wire bus;
  assign bus = en ? d : 1'bz;
  assign q = bus;
endmodule

// breadth: clean | An internal wire driven by a tri-state assignment and connected to an instance port is not reported.
// pair: internal-wire-vs-instance-connection
module sub(inout wire p);
endmodule
module top(input logic en, input logic d);
  wire bus;
  assign bus = en ? d : 1'bz;
  sub u(.p(bus));
endmodule

// breadth: reports | An internal wire with a single tri-state driver is reported.
// pair: single-vs-multiple-tristate-drivers
module top(input logic en, input logic d, output logic q);
  wire bus;
  assign bus = en ? d : 1'bz;
  assign q = bus;
endmodule

// breadth: clean | An internal wire driven by two tri-state drivers is not reported by the single-driver tri-state rule.
// pair: single-vs-multiple-tristate-drivers
module top(input logic en1, input logic en2, input logic d1, input logic d2, output logic q);
  wire bus;
  assign bus = en1 ? d1 : 1'bz;
  assign bus = en2 ? d2 : 1'bz;
  assign q = bus;
endmodule

// breadth: reports | An internal wire driven by a tri-state assignment with reversed ternary branch order is reported.
module top(input logic en, input logic d, output logic q);
  wire bus;
  assign bus = en ? 1'bz : d;
  assign q = bus;
endmodule

// breadth: clean | A purely undriven internal wire with no driver at all is not reported by the tri-state rule.
module top(output logic q);
  wire bus;
  assign q = bus;
endmodule

// breadth: clean | An internal wire driven by an instance output port is not reported by the tri-state rule.
module sub(output logic out);
endmodule
module top(output logic q);
  wire bus;
  sub u(.out(bus));
  assign q = bus;
endmodule
