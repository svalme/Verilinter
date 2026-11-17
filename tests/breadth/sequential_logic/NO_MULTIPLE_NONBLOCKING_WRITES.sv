// breadth: reports | Unconditional sibling nonblocking writes to the same variable are reported.
// pair: unconditional-vs-if-else
module top(input clk, input a, input b, output logic y);
  always_ff @(posedge clk) begin
    y <= a;
    y <= b;
  end
endmodule

// breadth: clean | Nonblocking writes to the same variable in mutually exclusive if-else branches are not reported.
// pair: unconditional-vs-if-else
module top(input clk, input rst_n, input d, output logic q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else q <= d;
  end
endmodule

// breadth: reports | Multiple nonblocking writes to the same bit-select in a block are reported.
// pair: same-bit-vs-different-bits
module top(input clk, input a, input b, output logic [1:0] y);
  always_ff @(posedge clk) begin
    y[0] <= a;
    y[0] <= b;
  end
endmodule

// breadth: clean | Nonblocking writes to provably disjoint bit-selects of a vector are not reported.
// pair: same-bit-vs-different-bits
module top(input clk, input a, input b, output logic [1:0] y);
  always_ff @(posedge clk) begin
    y[0] <= a;
    y[1] <= b;
  end
endmodule

// breadth: reports | Multiple nonblocking writes to the same scalar variable in a block are reported.
// pair: same-signal-vs-different-signals
module top(input clk, input a, input b, output logic y);
  always_ff @(posedge clk) begin
    y <= a;
    y <= b;
  end
endmodule

// breadth: clean | Nonblocking writes to distinct variables in the same sequential block are not reported.
// pair: same-signal-vs-different-signals
module top(input clk, input a, input b, output logic y, output logic z);
  always_ff @(posedge clk) begin
    y <= a;
    z <= b;
  end
endmodule

// breadth: reports | Sibling nonblocking writes to the same variable inside an if body are reported.
// pair: nested-sibling-vs-loop
module top(input clk, input en, input a, input b, output logic y);
  always_ff @(posedge clk) begin
    if (en) begin
      y <= a;
      y <= b;
    end
  end
endmodule

// breadth: clean | A nonblocking write within a for-loop iterating over an array slice is not reported.
// pair: nested-sibling-vs-loop
module top(input clk, input [3:0] d, output logic [3:0] q);
  always_ff @(posedge clk) begin
    for (int i = 0; i < 4; i = i + 1) begin
      q[i] <= d[i];
    end
  end
endmodule

// breadth: reports | Multiple nonblocking writes to the same unpacked array element are reported.
module top(input clk, input a, input b, output logic mem [1:0]);
  always_ff @(posedge clk) begin
    mem[0] <= a;
    mem[0] <= b;
  end
endmodule

// breadth: reports | Three nonblocking writes to the same target in straight-line sequential code are reported once.
module top(input clk, input a, input b, input c, output logic y);
  always_ff @(posedge clk) begin
    y <= a;
    y <= b;
    y <= c;
  end
endmodule

// breadth: clean | Nonblocking writes to the same variable across mutually exclusive case branches are not reported.
module top(input clk, input [1:0] sel, input d, output logic q);
  always_ff @(posedge clk) begin
    case (sel)
      2'b00: q <= 1'b0;
      2'b01: q <= d;
      default: q <= 1'b1;
    endcase
  end
endmodule

// breadth: clean | Nonblocking writes to provably disjoint elements of an unpacked array are not reported.
module top(input clk, input a, input b, output logic mem [1:0]);
  always_ff @(posedge clk) begin
    mem[0] <= a;
    mem[1] <= b;
  end
endmodule
