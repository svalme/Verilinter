// breadth: reports | A variable that is written and never read is write-only.
// pair: write-only-versus-read
module top(input logic i, output logic o);
  logic a;
  assign a = i;
  assign o = 1'b0;
endmodule

// breadth: clean | A variable that is written and read is not write-only.
// pair: write-only-versus-read
module top(input logic i, output logic o);
  logic a;
  assign a = i;
  assign o = a;
endmodule

// breadth: clean | A variable with neither writes nor reads belongs to UNUSED_VARIABLE.
// pair: declaration-initializer-write-only
module top(output logic o);
  logic a;
  assign o = 1'b0;
endmodule

// breadth: reports | A declaration initializer is a write event, so a variable never read is write-only.
// pair: declaration-initializer-write-only
module top(output logic o);
  logic a = 1'b0;
  assign o = 1'b0;
endmodule

// breadth: clean | Multiple reads of a written variable count as reads.
module top(input logic i, output logic o);
  logic a;
  assign a = i;
  always_comb o = a & a;
endmodule

// breadth: reports | A bit-select write without any read is write-only.
// pair: bit-select-use
module top(input logic i, output logic o);
  logic [3:0] v;
  assign v[0] = i;
  assign o = 1'b0;
endmodule

// breadth: clean | A bit-select read of a written variable is a read.
// pair: bit-select-use
module top(output logic o);
  logic [3:0] v;
  assign v = '0;
  assign o = v[2];
endmodule

// breadth: clean | A variable referenced in an explicit sensitivity list has a read use.
module top(input logic i, output logic o);
  logic a;
  always @(a) o = i;
  assign a = i;
endmodule

// breadth: clean | A variable read only in a concurrent assertion has a read use.
module top(input logic clk, input logic i, output logic o);
  logic a;
  assign a = i;
  assign o = 1'b0;
  assert property (@(posedge clk) a);
endmodule

// breadth: clean | A variable connected to an instance input port has a read use.
module sub(input logic p);
endmodule
module top(input logic i, output logic o);
  logic a;
  assign a = i;
  sub u(.p(a));
  assign o = 1'b0;
endmodule

// breadth: clean | A variable whose only writer is an instance output port and that nothing else reads is left to UNREAD_INSTANCE_OUTPUT, which names the instance and port.
module sub(output logic p);
  assign p = 1'b0;
endmodule
module top(output logic o);
  logic a;
  sub u(.p(a));
  assign o = 1'b0;
endmodule

// breadth: clean | A variable whose name marks it as intentionally unused is exempt from write-only reporting.
module top(input logic i, output logic o);
  logic unused_a;
  assign unused_a = i;
  assign o = 1'b0;
endmodule

// breadth: clean | An output port driven but not read within the module is not a variable of this rule.
module top(input logic i, output logic o);
  assign o = i;
endmodule

// breadth: reports | A function-local variable written but never read is write-only.
module top(input logic i, output logic o);
  function automatic logic f(input logic x);
    logic t;
    t = x;
    return 1'b0;
  endfunction
  assign o = f(i);
endmodule

// breadth: clean | A variable declared in a generate block and read through the block name is read.
module top(output logic o);
  if (1) begin : g
    logic x;
    assign x = 1'b1;
  end
  assign o = g.x;
endmodule

// breadth: clean | An indexed generate-loop path reaches the shared declaration and counts as a read.
module top(output logic o);
  for (genvar i = 0; i < 2; i++) begin : g
    logic x;
    assign x = 1'b1;
  end
  assign o = g[0].x;
endmodule

// breadth: clean | A hierarchical path through two module instances in the same source reaches the inner variable.
module leaf(input logic a);
  logic inner;
  assign inner = a;
endmodule
module mid(input logic a);
  leaf v(.a(a));
endmodule
module top(input logic i, output logic o);
  mid u(.a(i));
  assign o = u.v.inner;
endmodule

// breadth: clean | A hierarchical path through one module instance in the same source is a read.
module child(input logic a);
  logic inner;
  assign inner = a;
endmodule
module top(input logic i, output logic o);
  child u(.a(i));
  assign o = u.inner;
endmodule

// breadth: clean | An upward hierarchical reference by the enclosing module name reads the variable in that module.
module child(output logic y);
  assign y = top.p;
endmodule
module top(output logic o);
  logic p;
  assign p = 1'b1;
  child u(.y(o));
endmodule

// breadth: reports | A hierarchical path to an unresolvable member name does not read the variable in that scope.
module top(output logic o);
  if (1) begin : g
    logic x;
    assign x = 1'b1;
  end
  assign o = g.nope;
endmodule

// breadth: reports | A hierarchical read of a shadowed variable reads the member scope rather than the enclosing declaration.
module top(output logic o);
  logic x;
  assign x = 1'b0;
  if (1) begin : g
    logic x;
    assign x = 1'b1;
  end
  assign o = g.x;
endmodule

// breadth: reports | A variable written through a hierarchical path with no read is write-only.
module top(output logic o);
  if (1) begin : g
    logic x;
  end
  assign g.x = 1'b1;
  assign o = 1'b0;
endmodule

// breadth: clean | A two-segment hierarchical path through nested generate blocks reaches the inner variable declaration.
module top(output logic o);
  if (1) begin : g1
    if (1) begin : g2
      logic x;
      assign x = 1'b1;
    end
  end
  assign o = g1.g2.x;
endmodule

// breadth: clean | A hierarchical path through a named procedural block reaches its local variable.
module top(input logic i, output logic o, output logic o2);
  always_comb begin : blk
    logic t;
    t = i;
    o = 1'b0;
  end
  assign o2 = blk.t;
endmodule

// breadth: clean | A member select on a struct variable is not a hierarchical path.
module top(output logic o);
  struct packed { logic x; } s;
  assign s = '0;
  assign o = s.x;
endmodule

// breadth: clean | A path through an instance of an undefined module cannot be resolved and generates no spurious finding.
module top(input logic i, output logic o);
  undefined_mod u(.a(i));
  assign o = u.inner;
endmodule

// breadth: clean | An absolute hierarchical path from $root reads the variable in that module.
module child(output logic y);
  assign y = $root.top.p;
endmodule
module top(output logic o);
  logic p;
  assign p = 1'b1;
  child u(.y(o));
endmodule

// breadth: gap | A variable written by a local assign and never read is write-only even when an instance output also drives it, but the output port connection is recorded as a read of the variable, so the rule does not report it.
module sub(output logic p);
  assign p = 1'b0;
endmodule
module top(input logic i, output logic o);
  logic a;
  assign a = i;
  sub u(.p(a));
  assign o = 1'b0;
endmodule
