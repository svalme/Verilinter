module top(input logic clk);
  logic x;
  inout wire internal_bus;

  always_ff @(posedge clk) begin
    x <= 1'b1;
  end
endmodule
