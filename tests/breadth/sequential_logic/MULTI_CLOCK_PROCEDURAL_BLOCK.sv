// breadth: reports | Two positive clock edges in an event list are reported.
// pair: two-clocks-vs-clock-and-reset
module top(input clk1, input clk2, input d, output logic q);
  always @(posedge clk1 or posedge clk2) begin
    q <= d;
  end
endmodule

// breadth: clean | A clock edge and an asynchronous reset edge in an event list are not reported.
// pair: two-clocks-vs-clock-and-reset
module top(input clk, input rst_n, input d, output logic q);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else q <= d;
  end
endmodule

// breadth: reports | Both posedge and negedge of the same signal in an event list are reported.
// pair: both-edges-same-signal-vs-single-edge
module top(input a, input d, output logic q);
  always @(posedge a or negedge a) begin
    q <= d;
  end
endmodule

// breadth: clean | A single edge-triggered clock signal in an always_ff block is not reported.
// pair: both-edges-same-signal-vs-single-edge
module top(input clk, input d, output logic q);
  always_ff @(posedge clk) begin
    q <= d;
  end
endmodule

// breadth: reports | Two distinct clock signals in an event list are reported.
// pair: two-clocks-vs-two-resets
module top(input clk_a, input clk_b, input d, output logic q);
  always_ff @(posedge clk_a or posedge clk_b) begin
    q <= d;
  end
endmodule

// breadth: clean | A clock and two distinct asynchronous reset edges in an event list are not reported.
// pair: two-clocks-vs-two-resets
module top(input clk, input rst1_n, input rst2, input d, output logic q);
  always @(posedge clk or negedge rst1_n or posedge rst2) begin
    if (!rst1_n) q <= 1'b0;
    else if (rst2) q <= 1'b1;
    else q <= d;
  end
endmodule

// breadth: reports | Multiple clock edges in an always_ff event list are reported.
// pair: two-clocks-vs-iff-clause
module top(input clk1, input clk2, input d, output logic q);
  always_ff @(posedge clk1 or negedge clk2) begin
    q <= d;
  end
endmodule

// breadth: clean | A single clock edge qualified with an iff clause is not reported.
// pair: two-clocks-vs-iff-clause
module top(input clk, input enable, input d, output logic q);
  always_ff @(posedge clk iff enable) begin
    q <= d;
  end
endmodule

// breadth: reports | An event list with three clock signals is reported.
module top(input clk1, input clk2, input clk3, input d, output logic q);
  always @(posedge clk1 or posedge clk2 or posedge clk3) begin
    q <= d;
  end
endmodule

// breadth: clean | A combinational always_comb block without edge triggers is not reported.
module top(input a, input b, output logic y);
  always_comb begin
    y = a & b;
  end
endmodule

// breadth: clean | A single active-low clock with negedge clk is not reported.
module top(input clk_n, input d, output logic q);
  always_ff @(negedge clk_n) begin
    q <= d;
  end
endmodule
