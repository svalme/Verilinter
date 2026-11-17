// breadth: reports | Blocking assignment to a state signal in an always_ff block is reported.
// pair: blocking-vs-nonblocking-in-always-ff
module top(input clk, input d, output logic q);
  always_ff @(posedge clk) begin
    q = d;
  end
endmodule

// breadth: clean | Nonblocking assignment to a state signal in an always_ff block is not reported.
// pair: blocking-vs-nonblocking-in-always-ff
module top(input clk, input d, output logic q);
  always_ff @(posedge clk) begin
    q <= d;
  end
endmodule

// breadth: reports | Blocking assignment in an edge-triggered always block is reported.
// pair: clocked-always-vs-always-latch
module top(input clk, input d, output logic q);
  always @(posedge clk) begin
    q = d;
  end
endmodule

// breadth: clean | Blocking assignment in an always_latch block is not reported by the sequential rule.
// pair: clocked-always-vs-always-latch
module top(input en, input d, output logic q);
  always_latch begin
    if (en) q = d;
  end
endmodule

// breadth: reports | Blocking assignment inside a sequential loop body is reported.
// pair: blocking-body-vs-for-loop-header
module top(input clk, input [3:0] d, output logic [3:0] q);
  always_ff @(posedge clk) begin
    for (int i = 0; i < 4; i = i + 1) begin
      q[i] = d[i];
    end
  end
endmodule

// breadth: clean | Loop iterator assignments within a for-loop header in an always_ff block are not reported.
// pair: blocking-body-vs-for-loop-header
module top(input clk, input [3:0] d, output logic [3:0] q);
  always_ff @(posedge clk) begin
    for (int i = 0; i < 4; i = i + 1) begin
      q[i] <= d[i];
    end
  end
endmodule

// breadth: reports | Blocking assignment to sequential state is reported.
// pair: clocked-vs-combinational-always
module top(input clk, input d, output logic q);
  always_ff @(posedge clk) begin
    q = d;
  end
endmodule

// breadth: clean | Blocking assignment in an always_comb block is not reported.
// pair: clocked-vs-combinational-always
module top(input a, output logic y);
  always_comb begin
    y = a;
  end
endmodule

// breadth: reports | Blocking assignment to a block-local temporary inside an always_ff block is reported.
module top(input clk, input d, output logic q);
  always_ff @(posedge clk) begin
    logic temp;
    temp = d;
    q <= temp;
  end
endmodule

// breadth: reports | Multiple blocking assignments in a sequential block are reported.
// expect: 2
module top(input clk, input a, input b, output logic y, output logic z);
  always_ff @(posedge clk) begin
    y = a;
    z = b;
  end
endmodule

// breadth: clean | Nonblocking assignment in an edge-triggered always block is not reported.
module top(input clk, input d, output logic q);
  always @(posedge clk) begin
    q <= d;
  end
endmodule

// breadth: clean | Blocking assignment in an always @* block is not reported.
module top(input a, output logic y);
  always @* begin
    y = a;
  end
endmodule
