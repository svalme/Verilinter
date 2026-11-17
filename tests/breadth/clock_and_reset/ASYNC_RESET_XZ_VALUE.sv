// breadth: reports | An explicit 1'bx literal assigned in an asynchronous reset branch is reported.
// pair: explicit-x-vs-zero-in-reset
module top(input clk, input rst_n, input d, output logic q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'bx;
    else q <= d;
  end
endmodule

// breadth: clean | A deterministic 1'b0 literal assigned in an asynchronous reset branch is not reported.
// pair: explicit-x-vs-zero-in-reset
module top(input clk, input rst_n, input d, output logic q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else q <= d;
  end
endmodule

// breadth: reports | An explicit 1'bz literal assigned in an asynchronous reset branch is reported.
// pair: explicit-z-vs-tick-zero-in-reset
module top(input clk, input rst_n, input d, output logic q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'bz;
    else q <= d;
  end
endmodule

// breadth: clean | An unbased unsized '0 literal assigned in an asynchronous reset branch is not reported.
// pair: explicit-z-vs-tick-zero-in-reset
module top(input clk, input rst_n, input [7:0] d, output logic [7:0] q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= '0;
    else q <= d;
  end
endmodule

// breadth: reports | A vector literal with a partial x bit assigned in an async reset branch is reported.
// pair: partial-x-vs-binary-literal
module top(input clk, input rst_n, input [1:0] d, output logic [1:0] q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 2'b0x;
    else q <= d;
  end
endmodule

// breadth: clean | A fully deterministic binary literal assigned in an async reset branch is not reported.
// pair: partial-x-vs-binary-literal
module top(input clk, input rst_n, input [1:0] d, output logic [1:0] q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 2'b00;
    else q <= d;
  end
endmodule

// breadth: reports | An explicit x literal assigned in an asynchronous reset conditional is reported.
// pair: async-reset-vs-sync-reset-x-value
module top(input clk, input rst_n, input d, output logic q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'bx;
    else q <= d;
  end
endmodule

// breadth: clean | An explicit x literal assigned in a synchronous reset branch is not reported by the async reset rule.
// pair: async-reset-vs-sync-reset-x-value
module top(input clk, input rst, input d, output logic q);
  always_ff @(posedge clk) begin
    if (rst) q <= 1'bx;
    else q <= d;
  end
endmodule

// breadth: reports | Multiple explicit x and z literals assigned in an asynchronous reset branch are reported.
// expect: 2
module top(input clk, input rst_n, input a, input b, output logic y, output logic z);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      y <= 1'bx;
      z <= 1'bz;
    end else begin
      y <= a;
      z <= b;
    end
  end
endmodule

// breadth: clean | A reset value assigned from a parameter identifier whose value is x is not reported by the literal rule.
module top #(parameter RESET_VAL = 1'bx) (input clk, input rst_n, input d, output logic q);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= RESET_VAL;
    else q <= d;
  end
endmodule

// breadth: clean | A sequential block without an asynchronous reset branch is not reported.
module top(input clk, input d, output logic q);
  always_ff @(posedge clk) begin
    q <= d;
  end
endmodule
