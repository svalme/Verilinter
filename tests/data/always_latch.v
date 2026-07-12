module latch_example(input logic en, input logic d, output logic q);
  always_latch begin
    if (en) q = d;
  end
endmodule
