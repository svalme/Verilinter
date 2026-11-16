// case: reports | The same name declared twice in one module.
module top;
  logic [3:0] dup;
  logic [3:0] dup;
endmodule

// case: reports | The same name declared twice inside one block.
// pair: one-block-versus-two-blocks
module top(output logic o);
  always_comb begin
    automatic int x;
    automatic int x;
    o = 1'b0;
  end
endmodule

// case: clean | The same name declared once in each of two blocks.
// pair: one-block-versus-two-blocks
module top(input logic [3:0] a, b, output logic [3:0] o1, o2);
  always_comb begin : blk_a
    automatic int unsigned shift;
    shift = a;
    o1 = shift[3:0];
  end
  always_comb begin : blk_b
    automatic int unsigned shift;
    shift = b;
    o2 = shift[3:0];
  end
endmodule

// case: clean | An initial block and a final block each declare a variable of the same name.
module top;
  initial begin
    int fh;
    fh = 1;
  end
  final begin
    int fh;
    fh = 2;
  end
endmodule

// case: clean | Loop variables of two separate for loops.
module top(output logic [3:0] o);
  always_comb begin
    for (int i = 0; i < 2; i++) o[i] = 1'b0;
    for (int i = 2; i < 4; i++) o[i] = 1'b1;
  end
endmodule

// case: reports | A local variable that redeclares a module-level one in the same scope.
module top(output logic o);
  logic t;
  logic t;
  assign o = t;
endmodule
