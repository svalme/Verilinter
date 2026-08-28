module top(input wire a, output reg y);
  reg x;
  always @* begin
    x = a;
    y = 1'b0;
  end
endmodule
