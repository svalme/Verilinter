// breadth: reports | A declared variable with neither reads nor writes has no uses at all.
// pair: unreferenced-versus-read
module top(output logic o);
  logic a;
  assign o = 1'b0;
endmodule

// breadth: clean | A variable that is read has a recorded use.
// pair: unreferenced-versus-read
module top(output logic o);
  logic a;
  assign a = 1'b1;
  assign o = a;
endmodule

// breadth: clean | A variable that is written but never read has a use and belongs to NO_WRITE_ONLY_VARIABLE instead.
// pair: unreferenced-versus-write-only
module top(input logic i, output logic o);
  logic a;
  assign a = i;
  assign o = i;
endmodule

// breadth: reports | A second declarator in a shared declaration that is never referenced is reported on its own.
// pair: unreferenced-versus-write-only
module top(input logic i, output logic o);
  logic a, b;
  assign a = i;
  assign o = a;
endmodule

// breadth: clean | A declaration initializer counts as a write event, leaving the unreferenced variable to NO_WRITE_ONLY_VARIABLE.
// pair: declaration-initializer
module top(output logic o);
  logic a = 1'b0;
  assign o = 1'b0;
endmodule

// breadth: reports | Without a declaration initializer or any other reference, the variable has zero uses.
// pair: declaration-initializer
module top(output logic o);
  logic a;
  assign o = 1'b0;
endmodule

// breadth: reports | An input port that is never read or written has zero uses.
// pair: input-port-use
module top(input logic a, output logic o);
  assign o = 1'b0;
endmodule

// breadth: clean | An input port that is read has a use.
// pair: input-port-use
module top(input logic a, output logic o);
  assign o = a;
endmodule

// breadth: reports | An output port that is never driven or read has zero uses.
// pair: output-port-use
module top(output logic o);
endmodule

// breadth: clean | An output port that is driven has a write use.
// pair: output-port-use
module top(output logic o);
  assign o = 1'b0;
endmodule

// breadth: reports | An inout port with no references in the module has zero uses.
module top(inout wire io);
endmodule

// breadth: clean | A signal wired into a named instance port connection has a recorded use.
// pair: port-connection-use
module top(output logic o);
  logic a;
  sub u_sub(.p(a));
  assign o = 1'b0;
endmodule

// breadth: reports | An unreferenced sibling signal not wired to the instance has zero uses.
// pair: port-connection-use
module top(output logic o);
  logic a, b;
  sub u_sub(.p(a));
  assign o = 1'b0;
endmodule

// breadth: clean | An implicit named port connection (.a) records a use on the signal of the same name.
module top(output logic o);
  logic a;
  sub u_sub(.a);
  assign o = 1'b0;
endmodule

// breadth: gap | A wildcard port connection (.*) connects a matching input port without an identifier node in the instance, so the signal in the parent is still reported as unused.
// expect: 0
module sub(input logic a, output logic y);
  assign y = a;
endmodule
module top(input logic a, output logic y);
  sub u_sub(.*);
endmodule

// breadth: clean | A variable whose name contains the substring `unused` in any case is exempt as intentionally unused.
// pair: unused-name-exemption
module top(output logic o);
  logic unused_a;
  logic b_unused;
  logic My_UnUsEd_Sig;
  assign o = 1'b0;
endmodule

// breadth: reports | A near-miss name that does not contain the full substring `unused` is still reported.
// pair: unused-name-exemption
module top(output logic o);
  logic unuse_a;
  assign o = 1'b0;
endmodule

// breadth: clean | Parameters and localparams have parameter symbol kind and belong to NO_UNUSED_PARAMETER.
module top #(parameter P = 1)(output logic o);
  localparam LP = 2;
  assign o = 1'b0;
endmodule

// breadth: clean | A genvar has genvar symbol kind and is not checked as an ordinary variable.
module top(output logic o);
  genvar g;
  assign o = 1'b0;
endmodule

// breadth: clean | Typedef names and enum constants are not variable symbols.
module top(output logic o);
  typedef logic [3:0] nib_t;
  typedef enum logic {IDLE, RUN} state_e;
  assign o = 1'b0;
endmodule

// breadth: clean | A function's implicit return variable is never counted as unused, even when the function never assigns it and is never called.
// pair: function-return-versus-local
module top(input logic i, output logic o);
  function automatic logic f();
  endfunction
  assign o = i;
endmodule

// breadth: reports | An unreferenced local variable declared inside a function body has zero uses.
// pair: function-return-versus-local
module top(input logic i, output logic o);
  function automatic logic f();
    logic tmp;
  endfunction
  assign o = i;
endmodule

// breadth: reports | An unreferenced formal argument of a function has zero uses.
module top(input logic i, output logic o);
  function automatic logic f(input logic x, input logic y);
    return x;
  endfunction
  assign o = f(i, i);
endmodule

// breadth: reports | An unreferenced local variable declared inside a named procedural block has zero uses in its block scope.
// pair: block-scope-local
module top(output logic o);
  always_comb begin : blk
    logic x;
    o = 1'b0;
  end
endmodule

// breadth: clean | A block-scoped variable that is written and read inside its block has uses.
// pair: block-scope-local
module top(output logic o);
  always_comb begin : blk
    logic x;
    x = 1'b0;
    o = x;
  end
endmodule

// breadth: reports | An unreferenced variable declared inside a generate block is reported in that generate scope.
module top #(parameter W = 4)(output logic o);
  assign o = 1'b0;
  if (W == 4) begin : g
    logic x;
  end
endmodule

// breadth: reports | A variable that is never referenced is unused under every parameter value, so a generate branch that the default parameters switch off does not hide it.
// pair: switched-off-branch
module top #(parameter W = 4)(output logic o);
  assign o = 1'b0;
  if (W == 1) begin : g
    logic x;
  end
endmodule

// breadth: clean | A variable that is used inside the switched-off branch itself has uses.
// pair: switched-off-branch
module top #(parameter W = 4)(input logic i, output logic o);
  if (W == 1) begin : g
    logic x;
    assign x = i;
    assign o = x;
  end
endmodule

// breadth: clean | A variable used only as an index selector in a bit-select or array access is read.
module top(input logic [3:0] mem, output logic o);
  logic [1:0] idx;
  assign o = mem[idx];
endmodule

// breadth: clean | A variable referenced only in an explicit sensitivity list has a recorded read use.
module top(input logic a, output logic o);
  logic ev;
  always @(ev) o = a;
endmodule

// breadth: clean | Reading a member of a packed struct variable records a use on the struct variable.
// pair: struct-member-use
module top(output logic o);
  struct packed { logic x; } s;
  assign o = s.x;
endmodule

// breadth: reports | A packed struct variable with no member or whole-struct references has zero uses.
// pair: struct-member-use
module top(output logic o);
  struct packed { logic x; } s;
  assign o = 1'b0;
endmodule

// breadth: reports | An unpacked array that is never indexed or referenced as a whole has zero uses.
// pair: unpacked-array-use
module top(output logic [7:0] o);
  logic [7:0] mem [4];
  assign o = 8'd0;
endmodule

// breadth: clean | Indexing an element of an unpacked array records a use on the array symbol.
// pair: unpacked-array-use
module top(output logic [7:0] o);
  logic [7:0] mem [4];
  assign o = mem[0];
endmodule

// breadth: gap | A variable inside a generate block read via a hierarchical path (g.x) is used, but hierarchical lookup only resolves the base name and leaves the member with zero uses.
// expect: 0
module top(output logic o);
  if (1) begin : g
    logic x;
  end
  assign o = g.x;
endmodule
