module switch_primitive_demo(input a, input en, output y);
    cmos g0(y, a, en, en);
endmodule
