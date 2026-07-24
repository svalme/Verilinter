module top(input logic a, b, output logic y);
  always_comb begin
    unique if (a) y = b;
    else y = 1'b0;
  end
endmodule
