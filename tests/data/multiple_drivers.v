module top(input logic clk, input logic rst_n);
  logic x;

  always_ff @(posedge clk) begin
    x <= 1'b1;
  end

  always_ff @(negedge rst_n) begin
    x <= 1'b0;
  end
endmodule
