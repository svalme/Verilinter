module invocation_callee_demo;
    import "DPI-C" function int c_add(int a, int b);
    logic [31:0] result;
    always_comb result = c_add(1, 2);
endmodule
