// breadth: reports | A negedge-qualified signal in an async-reset block lacking an _n or _b suffix is reported.
// pair: negedge-rst-suffix-n
module top(input clk, input rst, input d, output logic q);
  always_ff @(posedge clk or negedge rst)
    if (!rst) q <= 1'b0;
    else q <= d;
endmodule

// breadth: clean | A negedge-qualified signal in an async-reset block ending in _n is not reported.
// pair: negedge-rst-suffix-n
module top(input clk, input rst_n, input d, output logic q);
  always_ff @(posedge clk or negedge rst_n)
    if (!rst_n) q <= 1'b0;
    else q <= d;
endmodule

// breadth: clean | A negedge-qualified signal in an async-reset block ending in _b is not reported.
module top(input clk, input reset_b, input d, output logic q);
  always_ff @(posedge clk or negedge reset_b)
    if (!reset_b) q <= 1'b0;
    else q <= d;
endmodule

// breadth: reports | A posedge-qualified signal in an async-reset block bearing an _n suffix is reported.
// pair: posedge-rst-suffix-n
module top(input clk, input rst_n, input d, output logic q);
  always_ff @(posedge clk or posedge rst_n)
    if (rst_n) q <= 1'b0;
    else q <= d;
endmodule

// breadth: clean | A posedge-qualified active-high reset without an _n or _b suffix is not reported.
// pair: posedge-rst-suffix-n
module top(input clk, input rst, input d, output logic q);
  always_ff @(posedge clk or posedge rst)
    if (rst) q <= 1'b0;
    else q <= d;
endmodule

// breadth: reports | A posedge-qualified reset bearing a _b suffix in an async block is reported.
// pair: sync-vs-async
module top(input clk, input rst_b, input d, output logic q);
  always_ff @(posedge clk or posedge rst_b)
    if (rst_b) q <= 1'b0;
    else q <= d;
endmodule

// breadth: clean | A synchronous sequential block with only one edge-qualified event is not checked.
// pair: sync-vs-async
module top(input clk, input rst_b, input d, output logic q);
  always_ff @(posedge clk)
    if (rst_b) q <= 1'b0;
    else q <= d;
endmodule

// breadth: clean | A combinational block without edge qualifiers is excluded from reset-naming checks.
module top(input a, input b, output logic y);
  always_comb y = a & b;
endmodule

// breadth: reports | A legacy always block with comma-separated edges and unsuffixed negedge reset is reported.
module top(input clk, input rst, input d, output reg q);
  always @(posedge clk, negedge rst)
    if (!rst) q <= 1'b0;
    else q <= d;
endmodule

// breadth: gap | An active-low clock triggers the reset-naming rule in an async block because the rule checks all edge signals.
// expect: 0
module top(input clk, input rst_n, input d, output logic q);
  always_ff @(negedge clk or negedge rst_n)
    if (!rst_n) q <= 1'b0;
    else q <= d;
endmodule
