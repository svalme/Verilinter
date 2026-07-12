module pragma_case_example(input logic [1:0] sel, output logic out);
  // synopsys full_case parallel_case
  case (sel)
    2'b00: out = 1'b0;
    2'b01: out = 1'b1;
  endcase
endmodule
