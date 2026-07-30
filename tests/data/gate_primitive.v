module gate_primitive_demo(input a, input b, output c, output d);
    and g0(c, a, b);
    or g1(d, a, b);
endmodule
