module delay_control_demo(input a, output b);
    assign #5 b = a;
endmodule
