module time_system_function_demo(output logic [63:0] t);
    always_comb t = $time;
endmodule
