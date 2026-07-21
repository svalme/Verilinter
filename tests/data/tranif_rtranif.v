module tranif_rtranif_demo (
    inout wire a,
    inout wire b,
    inout wire c,
    inout wire d,
    input wire e,
    input wire f,
    input wire g,
    input wire h
);
    tranif1 t0(a, b, e);
    tranif0 t1(c, d, f);
    rtranif1 t2(a, c, g);
    rtranif0 t3(b, d, h);
endmodule
