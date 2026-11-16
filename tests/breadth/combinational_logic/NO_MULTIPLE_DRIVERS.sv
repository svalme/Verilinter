// breadth: reports | One variable written by two always_comb blocks.
module top(input logic a, b, output logic y);
  always_comb y = a;
  always_comb y = b;
endmodule

// breadth: clean | Variables with the same name declared inside two different blocks are two variables.
// pair: shared-versus-block-local
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

// breadth: reports | The same name written from two blocks when it is declared once, outside them.
// pair: shared-versus-block-local
module top(input logic [3:0] a, b, output logic [3:0] o1, o2);
  int unsigned shift;
  always_comb begin : blk_a
    shift = a;
    o1 = shift[3:0];
  end
  always_comb begin : blk_b
    shift = b;
    o2 = shift[3:0];
  end
endmodule

// breadth: clean | An initial block and a final block each declare their own file handle.
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

// breadth: clean | Different bits of one vector written by different blocks.
module top(input logic a, b, output logic [1:0] y);
  always_comb y[0] = a;
  always_comb y[1] = b;
endmodule
