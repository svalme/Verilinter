module top(input logic sel, output logic y);
  always_comb begin
    unique0 case (sel)
      1'b0: y = 1'b0;
      default: y = 1'b1;
    endcase
  end
endmodule
