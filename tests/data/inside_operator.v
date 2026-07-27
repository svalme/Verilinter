module top(input logic [1:0] sel, output logic y);
  always_comb begin
    y = (sel inside {2'b00, 2'b01}) ? 1'b1 : 1'b0;
  end
endmodule
