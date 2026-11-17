// breadth: reports | A module parameter that is never referenced is unused.
// pair: module-parameter-use
module top #(parameter WIDTH = 4)(input logic i, output logic o);
  assign o = i;
endmodule

// breadth: clean | A module parameter referenced in an expression is used.
// pair: module-parameter-use
module top #(parameter WIDTH = 4)(input logic [WIDTH-1:0] i, output logic o);
  assign o = i[0];
endmodule

// breadth: reports | An in-body parameter declaration that is never referenced is unused.
// pair: in-body-parameter-use
module top(input logic i, output logic o);
  parameter DEPTH = 8;
  assign o = i;
endmodule

// breadth: clean | An in-body parameter declaration referenced in logic is used.
// pair: in-body-parameter-use
module top(input logic i, output logic [7:0] o);
  parameter DEPTH = 8;
  assign o = {DEPTH{i}};
endmodule

// breadth: reports | A localparam that is never referenced is unused.
// pair: localparam-use
module top(input logic i, output logic o);
  localparam LIMIT = 10;
  assign o = i;
endmodule

// breadth: clean | A localparam referenced in an expression is used.
// pair: localparam-use
module top(input logic i, output logic [7:0] o);
  localparam LIMIT = 10;
  assign o = 8'(LIMIT);
endmodule

// breadth: clean | A parameter used to initialize a subsequent parameter has a read use.
module top #(parameter BASE = 4, parameter TOTAL = BASE * 2)(input logic [TOTAL-1:0] i, output logic o);
  assign o = i[0];
endmodule

// breadth: clean | A parameter declared in a package is not reported because uses from other files are not tracked.
package pkg;
  parameter int MAX_COUNT = 16;
endpackage
module top(output logic o);
  assign o = 1'b0;
endmodule

// breadth: clean | A parameter named with unused is exempt from unused reporting.
module top #(parameter UNUSED_PAD = 0)(input logic i, output logic o);
  assign o = i;
endmodule

// breadth: clean | An unreferenced variable is not a parameter and belongs to UNUSED_VARIABLE.
module top(output logic o);
  logic unused_v;
  assign o = 1'b0;
endmodule

// breadth: clean | A parameter used only in a generate condition has a read use.
module top #(parameter ENABLE_EXTRA = 1)(input logic i, output logic o);
  if (ENABLE_EXTRA) begin : g
    assign o = i;
  end else begin : g
    assign o = ~i;
  end
endmodule

// breadth: reports | Multiple unreferenced parameters in the parameter port list are each reported.
// expect: 2
module top #(parameter P1 = 1, parameter P2 = 2, parameter USED = 4)(input logic [USED-1:0] i, output logic o);
  assign o = i[0];
endmodule

// breadth: reports | A localparam used only by an unused localparam is itself used, so only the last one is reported.
module top(output logic o);
  localparam A = 1;
  localparam B = A + 1;
  assign o = 1'b0;
endmodule

// breadth: clean | A parameter used only in an instance parameter override has a read use.
module child #(parameter W = 4)(input logic [W-1:0] a);
  wire x = a[0];
endmodule
module top #(parameter P = 4)(input logic [3:0] a);
  child #(.W(P)) u(.a(a));
endmodule

// breadth: reports | A parameter that a parent overrides but the child module never uses is still unused in the child.
module child #(parameter W = 4)(input logic a);
endmodule
module top(input logic a);
  child #(.W(8)) u(.a(a));
endmodule

// breadth: clean | A parameter used only in a concurrent assertion has a read use.
module top #(parameter N = 2)(input logic clk, input logic [3:0] a);
  assert property (@(posedge clk) a < N);
endmodule

// breadth: gap | A type parameter that is never used is unused, but only value parameters are checked.
module top #(parameter type T = logic)(input logic i, output logic o);
  assign o = i;
endmodule
