module unique0_if_demo(input logic [1:0] sel, output logic y);
    always_comb begin
        unique0 if (sel == 2'b00) y = 1'b1;
        else if (sel == 2'b01) y = 1'b0;
    end
endmodule
