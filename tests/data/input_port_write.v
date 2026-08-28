module top(input wire a, output reg y);
  reg z;
  always @* begin
    a = z;
    y = z;
  end
endmodule
