module top(input logic clk, input logic sel, input logic a, input logic b);
  logic x, y;

  always @(posedge clk) begin
    x <= a;
    y = b;
  end

  always_comb begin
    casez (sel)
      1'b0: x = a;
      default: x = b;
    endcase
  end
endmodule
