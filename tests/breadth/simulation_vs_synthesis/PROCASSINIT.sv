// breadth: reports | A variable initialized at declaration and assigned in an always_ff block is reported.
// pair: declaration-initializer
module top(input clk, input d);
  logic flop = 1'b0;
  always_ff @(posedge clk) flop <= d;
endmodule

// breadth: clean | A sequential flop declared without an initializer is not reported.
// pair: declaration-initializer
module top(input clk, input d);
  logic flop;
  always_ff @(posedge clk) flop <= d;
endmodule

// breadth: reports | A variable initialized at declaration and assigned in an always_comb block is reported.
// pair: initial-vs-procedural
module top(input in);
  logic c = 1'b0;
  always_comb c = in;
endmodule

// breadth: clean | A variable initialized at declaration and assigned only in an initial block is clean.
// pair: initial-vs-procedural
module top;
  logic flop = 1'b0;
  initial flop = 1'b1;
endmodule

// breadth: reports | A variable initialized at declaration and assigned in an always_latch block is reported.
// pair: latch-procedural
module top(input en, input in);
  logic l = 1'b0;
  always_latch if (en) l = in;
endmodule

// breadth: clean | A latch variable declared without an initializer is not reported.
// pair: latch-procedural
module top(input en, input in);
  logic l;
  always_latch if (en) l = in;
endmodule

// breadth: reports | A legacy reg initialized at declaration and assigned in always @(posedge clk) is reported.
module top(input clk, input d);
  reg r = 1'b0;
  always @(posedge clk) r <= d;
endmodule

// breadth: clean | A local variable initialized inside a function body is excluded from the check.
module top(input in, output logic out);
  function automatic logic f(logic x);
    logic tmp = 1'b0;
    tmp = x;
    return tmp;
  endfunction
  assign out = f(in);
endmodule

// breadth: clean | A local variable initialized inside a task body is excluded from the check.
module top(input in, output logic out);
  task automatic t(input logic x, output logic y);
    logic tmp = 1'b0;
    tmp = x;
    y = tmp;
  endtask
  always_comb t(in, out);
endmodule

// breadth: clean | A variable initialized at declaration that is never procedurally assigned is clean.
module top(output logic out);
  logic v = 1'b1;
  assign out = v;
endmodule

// breadth: gap | The finding is wrong: a net initialized at declaration and driven by a continuous assignment has no procedural assignment, but it is reported as one (the double drive is a separate problem that no rule reports).
// expect: 0
module top(input in);
  wire w = 1'b0;
  assign w = in;
endmodule

// breadth: clean | A loop variable declared in a for-loop header is initialized by the loop itself, so the loop step is not a procedural write to an initialized variable.
// pair: loop-variable-declaration-site
module top(input logic [3:0] a, output logic [3:0] o);
  always_comb begin
    for (int i = 0; i < 4; i++) o[i] = a[i];
  end
endmodule

// breadth: reports | A variable declared outside the loop with an initializer and then used as the loop variable is initialized at declaration and written by the loop.
// pair: loop-variable-declaration-site
module top(input logic [3:0] a, output logic [3:0] o);
  integer i = 0;
  always_comb begin
    for (i = 0; i < 4; i = i + 1) o[i] = a[i];
  end
endmodule

// breadth: clean | A typed loop variable declared in a for-loop header of a clocked block is not reported.
module top(input logic clk, input logic [3:0] a, output logic [3:0] o);
  always_ff @(posedge clk) begin
    for (int unsigned i = 0; i < 4; i++) o[i] <= a[i];
  end
endmodule

// breadth: clean | Every loop variable declared in the headers of nested for loops is exempt, not only the outer one.
module top(input logic [15:0] a, output logic [15:0] o);
  always_comb begin
    for (int i = 0; i < 4; i++)
      for (int j = 0; j < 4; j++) o[i*4+j] = a[i*4+j];
  end
endmodule

// breadth: clean | A loop variable that the loop body also changes is still the loop variable declared in the header.
module top(input logic [7:0] a, output logic [7:0] o);
  always_comb begin
    o = '0;
    for (int i = 0; i < 8; i++) begin
      if (a[i]) i = i + 1;
      o[i] = 1'b1;
    end
  end
endmodule

// breadth: clean | A genvar in a generate for-loop header is not a variable with a procedural write.
module top(input logic [3:0] a, output logic [3:0] o);
  for (genvar g = 0; g < 4; g++) begin : gl
    assign o[g] = a[g];
  end
endmodule
