// breadth: reports | An input port that is written and never read is write-only.
// pair: write-only-versus-read
module top(input logic a, output logic o);
  always_comb begin
    a = 1'b0;
    o = 1'b0;
  end
endmodule

// breadth: clean | An input port that is written and read once is not write-only.
// pair: write-only-versus-read
module top(input logic a, output logic o);
  always_comb begin
    a = 1'b0;
    o = a;
  end
endmodule

// breadth: reports | An input port written by continuous assignment and never read is write-only.
// pair: unreferenced-versus-write-only
module top(input logic a, output logic o);
  assign a = 1'b0;
  assign o = 1'b0;
endmodule

// breadth: clean | An input port with neither writes nor reads belongs to UNUSED_VARIABLE.
// pair: unreferenced-versus-write-only
module top(input logic a, output logic o);
  assign o = 1'b0;
endmodule

// breadth: reports | A bit-select write to an input port without any read is write-only.
// pair: bit-select-use
module top(input logic [3:0] a, output logic o);
  always_comb begin
    a[0] = 1'b1;
    o = 1'b0;
  end
endmodule

// breadth: clean | A bit-select read of a partially written input port counts as a read.
// pair: bit-select-use
module top(input logic [3:0] a, output logic o);
  always_comb begin
    a[0] = 1'b1;
    o = a[1];
  end
endmodule

// breadth: clean | An output port written but never read inside the module is not an input port.
module top(output logic o);
  assign o = 1'b0;
endmodule

// breadth: clean | An inout port is not an input port and is not flagged as a write-only input port.
module top(inout wire io, output logic o);
  assign io = 1'b0;
  assign o = 1'b0;
endmodule

// breadth: clean | An internal variable written but never read is not an input port.
module top(output logic o);
  logic a;
  assign a = 1'b0;
  assign o = 1'b0;
endmodule

// breadth: clean | An input port written and read only in a concurrent assertion has a read use.
module top(input logic clk, input logic a, output logic o);
  always_comb begin
    a = 1'b0;
    o = 1'b0;
  end
  assert property (@(posedge clk) a);
endmodule

// breadth: clean | An input port written and referenced in an explicit sensitivity list has a read use.
module top(input logic a, output logic o);
  always @(a) begin
    o = 1'b0;
  end
  assign a = 1'b1;
endmodule

// breadth: clean | An input port written and passed to a sub-module input port has a read use.
module sub(input logic p);
endmodule
module top(input logic a, output logic o);
  sub u(.p(a));
  assign a = 1'b0;
  assign o = 1'b0;
endmodule

// breadth: reports | Comma-grouped ANSI input ports written but not read are write-only.
// expect: 2
module top(input logic a, b, c, output logic o);
  always_comb begin
    a = 1'b1;
    b = 1'b1;
    o = c;
  end
endmodule
