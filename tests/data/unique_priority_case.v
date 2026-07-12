module unique_priority_case_example(input logic [1:0] sel, output logic y);
  always_comb begin
    unique case (sel)
      2'b00: y = 1'b0;
      default: y = 1'b1;
    endcase

    priority case (sel)
      2'b01: y = 1'b0;
      default: y = 1'b1;
    endcase
  end
endmodule
