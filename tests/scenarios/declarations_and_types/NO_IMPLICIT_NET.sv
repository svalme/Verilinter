// scenario: reports | A name that is never declared.
// pair: undeclared-versus-path-base
module top(input logic a, output logic o);
  assign o = missing_net & a;
endmodule

// scenario: clean | The first segment of a hierarchical path to a generate block is a scope, not a net.
// pair: undeclared-versus-path-base
module top(input logic a, output logic z);
  if (1) begin : g_blk
    logic t;
    assign t = a;
  end
  assign z = g_blk.t;
endmodule

// scenario: reports | An undeclared name outside a path is a net even when the same name is also used as a path base.
module top(output logic z);
  assign z = missing_net.t;
  assign z = missing_net;
endmodule

// scenario: clean | A task called with no arguments is a call, not a net.
module top;
  reg clk;
  task spi_action;
    clk = 1;
  endtask
  initial begin
    spi_action;
  end
endmodule

// scenario: clean | A name an import could supply from a package no analysed file declares.
module top import other_pkg::*; (output logic o);
  assign o = FROM_OTHER;
endmodule

// scenario: reports | An undeclared name when every imported package is known.
package p_pkg;
  localparam int Known = 1;
endpackage
module top import p_pkg::*; (output logic o);
  assign o = Known;
  assign o = missing_net;
endmodule
