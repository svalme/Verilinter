// breadth: reports | A module without a preceding timescale directive is reported.
// pair: timescale-present
module top;
endmodule

// breadth: clean | A module preceded by a timescale directive is not reported.
// pair: timescale-present
`timescale 1ns/1ps
module top;
endmodule

// breadth: reports | A timescale directive placed after the module does not cover the module.
// pair: timescale-placement
module top;
endmodule
`timescale 1ns/1ps

// breadth: clean | Comments between a timescale directive and the module do not hide the directive.
// pair: timescale-placement
`timescale 1ns/1ps
// Header comments
// Additional comment line
module top;
endmodule

// breadth: reports | A file with two modules and no timescale reports on the first module.
// pair: multi-module-timescale
module first;
endmodule
module second;
endmodule

// breadth: clean | A file with a timescale directive followed by multiple modules is clean.
// pair: multi-module-timescale
`timescale 1ns/1ps
module first;
endmodule
module second;
endmodule

// breadth: clean | A package declaration without a timescale directive is not reported.
package p;
  localparam int P = 1;
endpackage

// breadth: clean | An interface declaration without a timescale directive is not reported.
interface itf;
  logic clk;
endinterface
