module top(input logic [1:0] sel, output logic y);
  always_comb begin
    case (sel) inside
      2'b00: y = 1'b0;
      default: y = 1'b1;
    endcase
  end
endmodule
