// breadth: reports | An asynchronous reset read in the data path of the clocked block is reported.
// pair: datapath-vs-reset-condition
module top(input clk, input rst_n, input d, output logic q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else q <= d & rst_n;
  end
endmodule

// breadth: clean | An asynchronous reset read only in the reset branch condition is not reported.
// pair: datapath-vs-reset-condition
module top(input clk, input rst_n, input d, output logic q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else q <= d;
  end
endmodule

// breadth: reports | An asynchronous reset read in a continuous assignment expression is reported.
// pair: continuous-assign-data-vs-port-connection
module top(input clk, input rst_n, input d, output logic q, output logic y);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else q <= d;
  end
  assign y = rst_n & d;
endmodule

// breadth: clean | An asynchronous reset passed to a submodule port connection is not reported.
// pair: continuous-assign-data-vs-port-connection
module child(input clk, input rst_n);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin end
  end
endmodule
module top(input clk, input rst_n);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin end
  end
  child u(.clk(clk), .rst_n(rst_n));
endmodule

// breadth: reports | An asynchronous reset read as an operand in an arithmetic datapath is reported.
// pair: async-reset-vs-sync-reset-datapath
module top(input clk, input rst_n, input [7:0] d, output logic [7:0] q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 8'h00;
    else q <= d + {7'b0, rst_n};
  end
endmodule

// breadth: clean | A synchronous reset signal read in the data path of a synchronous block is not reported.
// pair: async-reset-vs-sync-reset-datapath
module top(input clk, input rst, input [7:0] d, output logic [7:0] q);
  always_ff @(posedge clk) begin
    if (rst) q <= 8'h00;
    else q <= d + {7'b0, rst};
  end
endmodule

// breadth: reports | An asynchronous reset passed as an argument to a datapath function is reported.
// pair: function-call-data-vs-clean-datapath
module top(input clk, input rst_n, input d, output logic q);
  function automatic logic f(input logic r);
    return ~r;
  endfunction
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else q <= f(rst_n);
  end
endmodule

// breadth: clean | A datapath function call using only data inputs is not reported.
// pair: function-call-data-vs-clean-datapath
module top(input clk, input rst_n, input d, output logic q);
  function automatic logic f(input logic x);
    return ~x;
  endfunction
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else q <= f(d);
  end
endmodule

// breadth: reports | An active-high asynchronous reset read as an operand in the datapath is reported.
module top(input clk, input rst, input d, output logic q);
  always_ff @(posedge clk or posedge rst) begin
    if (rst) q <= 1'b0;
    else q <= d | rst;
  end
endmodule

// breadth: reports | An asynchronous reset read as data in a separate combinational block is reported.
module top(input clk, input rst_n, input d, output logic q, output logic y);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else q <= d;
  end
  always_comb begin
    y = d & rst_n;
  end
endmodule

// breadth: clean | An active-high asynchronous reset used only in the reset branch condition is not reported.
module top(input clk, input rst, input d, output logic q);
  always_ff @(posedge clk or posedge rst) begin
    if (rst) q <= 1'b0;
    else q <= d;
  end
endmodule

// breadth: clean | A synchronous block with no asynchronous reset in its sensitivity list is not reported.
module top(input clk, input d, output logic q);
  always_ff @(posedge clk) begin
    q <= d;
  end
endmodule
