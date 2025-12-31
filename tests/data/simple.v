module top(input logic clk);
  real x;
  always @(posedge clk) begin
    a = b;
    c <= d;
  end
  always_comb begin
    y <= z;
  end
  case(sel)
    0: out = a;
  endcase
endmodule
