module random_system_function_demo(output logic [31:0] r);
    always_comb r = $random;
endmodule
