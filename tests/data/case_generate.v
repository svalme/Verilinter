module case_generate_example(input logic sel, output logic y);
  generate
    case (sel)
      1'b0: begin
        assign y = 1'b0;
      end
      default: begin
        assign y = 1'b1;
      end
    endcase
  endgenerate
endmodule
