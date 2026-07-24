module top(input logic a, b, c, output logic y);
  always_comb begin
    priority if (a) y = b;
    else y = c;
  end
endmodule
